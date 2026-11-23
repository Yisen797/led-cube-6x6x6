/* ============================================================================
 *  6 × 6 × 6 蓝光 LED 光立方 —— ESP32 DevKit V1 固件（4 位灰度版）
 *  ----------------------------------------------------------------------------
 *  硬件接口约定（驱动部分由使用者自行实现，固件只负责按这个约定输出）：
 *
 *  5 根控制线：
 *      DATA  ── 串行数据，接第一片 74HCT595 的 SER
 *      CLK   ── 移位时钟，接所有 595 的 SRCLK
 *      LATCH ── 锁存，接所有 595 的 RCLK
 *      SRCLR ── 低有效清零，接所有 595 的 /SRCLR
 *      OE    ── 低有效输出使能，接所有 595 的 /OE
 *
 *  7 片 74HCT595 级联成 56 bit（6×6×6 版本）：
 *      ESP32 DATA → U1(层寄存器) → U2(第0行) → U3(第1行) → … → U7(第5行)
 *
 *  数据约定：
 *      行字节 bit x = 1  → 坐标 (x, y) 那根列线导通（灌电流）
 *      层字节 bit z = 1  → 第 z 层阳极加电
 *      行寄存器 y 的 bit x     对应列 (x, y)
 *      层寄存器 bit z          对应第 z 层（z = 0 在最下面）
 *      每片 595 的 bit6、bit7 没有用到，恒为 0
 *
 *  ----------------------------------------------------------------------------
 *  灰度原理（BCM：Binary Code Modulation）
 *
 *  每个像素 4 bit 亮度 0..15。扫描一层时，把该层拆成 4 个子场，
 *  子场 b 的持续时间正比于 2^b：
 *
 *      子场 b=3(最高位)  ████████████████   8 份
 *      子场 b=2          ████████           4 份
 *      子场 b=1          ████               2 份
 *      子场 b=0(最低位)  ██                 1 份
 *      合计 15 份 ≈ 825 us，6 层 ≈ 5 ms → 约 200 Hz
 *
 *  某个子场只点亮“亮度值该位为 1”的像素，人眼积分后得到 0..15 级亮度。
 * ==========================================================================*/

#include <Arduino.h>
#include <math.h>

/* ============================== 尺寸 ==================================== */
#define N 6                     /* 6 × 6 × 6；想换尺寸改这里（同时要改驱动板接线） */
#define BOX (N * N * N)         /* 216 */

/* ============================== 引脚定义 ================================= */
#define PIN_DATA   23      /* VSPI MOSI */
#define PIN_CLK    18      /* VSPI SCK  */
#define PIN_LATCH   5
#define PIN_SRCLR  17      /* 原理图 H9-9，ESP32 右排第 9 脚 */
#define PIN_OE     16      /* 原理图 H9-10，ESP32 右排第 10 脚 */

/* ============================ 灰度参数 ================================== */
#define GRAY_BITS   4                          /* 4 bit = 16 级 */
#define GRAY_LEVELS ((1 << GRAY_BITS) - 1)     /* 15 份 */
/* 一帧目标 5000 us，平分给 N 层 × 15 份 */
#define UNIT_US     (5000 / (N * GRAY_LEVELS)) /* 6×6×6 → 55 us */

/* ============================== 帧缓冲 ================================== */
/* lum[z][x][y] = 0..15 亮度；0 = 灭，15 = 最亮 */
static uint8_t lum[N][N][N];

/* ======================= 底层：直接写 GPIO 寄存器 ======================== */
/* 引脚号都 < 32，可以直接操作 out_w1ts / out_w1tc，比 digitalWrite 快很多 */
static inline void pinHi(int p) { GPIO.out_w1ts = (1UL << p); }
static inline void pinLo(int p) { GPIO.out_w1tc = (1UL << p); }

/* 移出一个字节（MSB 先出） */
static inline void shiftByte(uint8_t b)
{
    for (int i = 7; i >= 0; --i) {
        if (b & (1u << i)) pinHi(PIN_DATA);
        else               pinLo(PIN_DATA);
        pinHi(PIN_CLK);
        pinLo(PIN_CLK);
    }
}

static inline void latchPulse(void)
{
    pinHi(PIN_LATCH);
    pinLo(PIN_LATCH);
}

/* ====================== 渲染一个子场（层 z，位 b） ====================== */
static void renderPlane(uint8_t z, int8_t b)
{
    /* 先送出的字节会停在链尾，所以按 行5 → 行0 → 层 的顺序发送 */
    for (int y = N - 1; y >= 0; --y) {
        uint8_t col = 0;
        for (int x = 0; x < N; ++x)
            if ((lum[z][x][y] >> b) & 1u) col |= (uint8_t)(1u << (x + 1));  /* 硬件用 Q1..Q6，Q0 空 */
        shiftByte(col);
    }
    /* 层是 P-MOS 高边开关（AO3401A）：595 输出 **低** → 栅极被拉低 → 导通。
       所以只有“当前层”送 0，其余 5 层都送 1（关断）；Q0/Q7 恒 0。
       注意：上电 /SRCLR 清零后输出全 0 会让 6 层全导通，靠列全 0 保证不亮，
       且 /OE 上拉（RP1–RP6）在 MCU 未初始化时把栅极拉到 5 V，层全部关断。 */
    shiftByte((uint8_t)(0x7Eu & ~(1u << (z + 1))));
    latchPulse();
}

/* 测一次“渲染子场”本身要多久（不含点亮保持时间），用来做时间补偿 */
static uint16_t g_planeUs = 0;

static void measurePlaneTime(void)
{
    uint32_t t0 = micros();
    for (int i = 0; i < 8; ++i) {
        for (uint8_t z = 0; z < N; ++z)
            for (int8_t b = GRAY_BITS - 1; b >= 0; --b)
                renderPlane(z, b);
    }
    g_planeUs = (uint16_t)((micros() - t0) / (8 * N * GRAY_BITS));
    if (g_planeUs > 60) g_planeUs = 60;
}

/* 扫描一整帧：N 层 × 4 个子场 */
static void renderFrame(void)
{
    for (uint8_t z = 0; z < N; ++z) {
        for (int8_t b = GRAY_BITS - 1; b >= 0; --b) {
            renderPlane(z, b);
            /* 子场保持时间 = 权重 × 单位 − 下一次移位占用，保证亮度比例准确 */
            int32_t hold = (int32_t)((1u << b) * UNIT_US) - (int32_t)g_planeUs;
            if (hold < 4) hold = 4;
            delayMicroseconds((uint16_t)hold);
        }
    }
}

/* ============================== 帧缓冲工具 ============================== */
static inline void clearLum(void) { memset(lum, 0, sizeof(lum)); }

static inline void setPx(int x, int y, int z, uint8_t v)
{
    if ((unsigned)x < N && (unsigned)y < N && (unsigned)z < N)
        lum[z][x][y] = (v > 15) ? 15 : v;
}

static inline void setPx(int x, int y, int z) { setPx(x, y, z, 15); }

/* ============================== 动画 ==================================== */
/* 所有动画只负责往 lum[][] 里写 0..15 的亮度 */

/* ---- 0. 雨滴（亮头 + 暗尾） ---- */
static uint8_t  rainZ[N][N];                /* 0xFF = 该列当前没有雨滴 */
static uint32_t rainTick = 0;

static void animRain(uint32_t t)
{
    if (t - rainTick >= 70) {
        rainTick = t;
        for (int x = 0; x < N; ++x)
            for (int y = 0; y < N; ++y) {
                if (rainZ[x][y] == 0xFF) {
                    if (random(100) < 12) rainZ[x][y] = N - 1;
                } else if (rainZ[x][y] == 0) {
                    rainZ[x][y] = 0xFF;     /* 落地消失 */
                } else {
                    rainZ[x][y]--;          /* 下落一层 */
                }
            }
    }
    for (int x = 0; x < N; ++x)
        for (int y = 0; y < N; ++y) {
            uint8_t z = rainZ[x][y];
            if (z != 0xFF) {
                setPx(x, y, z, 15);
                if (z < N - 1) setPx(x, y, z + 1, 4);   /* 暗拖尾 */
            }
        }
}

/* ---- 1. 呼吸球壳 ---- */
static void animSphere(uint32_t t)
{
    const float c = (N - 1) * 0.5f;            /* 2.5 */
    float r = c + (c - 0.4f) * sinf(t * 0.0012f);
    for (int z = 0; z < N; ++z)
        for (int x = 0; x < N; ++x)
            for (int y = 0; y < N; ++y) {
                float dx = x - c, dy = y - c, dz = z - c;
                float d  = sqrtf(dx * dx + dy * dy + dz * dz);
                if (fabsf(d - r) < 0.85f) setPx(x, y, z, 15);
            }
}

/* ---- 2. 平面扫描（亮面 + 暗拖尾） ---- */
static void animSweep(uint32_t t)
{
    int z = (t / 110) % N;
    for (int x = 0; x < N; ++x)
        for (int y = 0; y < N; ++y) {
            setPx(x, y, z, 15);
            if (z > 0) setPx(x, y, z - 1, 5);
        }
}

/* ---- 3. 随机星光（随机亮度） ---- */
static uint8_t tw[N][N][N];

static void animTwinkle(uint32_t t)
{
    static uint32_t last = 0;
    if (t - last >= 85) {
        last = t;
        memset(tw, 0, sizeof(tw));
        for (int i = 0; i < 14; ++i) {
            int x = random(N), y = random(N), z = random(N);
            tw[z][x][y] = (uint8_t)(4 + random(12));   /* 4..15 */
        }
    }
    memcpy(lum, tw, sizeof(lum));
}

/* ---- 4. 立方体边框（12 条棱） ---- */
static void animCubeFrame(void)
{
    for (int i = 0; i < N; ++i)
        for (int a = 0; a < N; ++a) {
            setPx(i, a, 0); setPx(i, a, N - 1);
            setPx(i, 0, a); setPx(i, N - 1, a);
            setPx(0, i, a); setPx(N - 1, i, a);
        }
}

/* ---- 5. 水波（亮度随相位变化） ---- */
static void animWave(uint32_t t)
{
    const float c = (N - 1) * 0.5f;
    uint8_t lvl = (uint8_t)(5 + 10 * (0.5f + 0.5f * sinf(t * 0.004f)));
    for (int x = 0; x < N; ++x)
        for (int y = 0; y < N; ++y) {
            float v = c + (c - 0.3f) * sinf(x * 0.95f + y * 0.95f + t * 0.004f);
            int   z = (int)lroundf(v);
            if (z >= 0 && z < N) setPx(x, y, z, lvl);
        }
}

/* ---- 6. 径向渐变（专门展示灰度：中心到边缘逐级变暗） ---- */
static void animGradient(uint32_t t)
{
    const float c = (N - 1) * 0.5f;
    float r0 = c * 0.5f + c * 0.8f * (0.5f + 0.5f * sinf(t * 0.0015f));
    for (int z = 0; z < N; ++z)
        for (int x = 0; x < N; ++x)
            for (int y = 0; y < N; ++y) {
                float dx = x - c, dy = y - c, dz = z - c;
                float d  = sqrtf(dx * dx + dy * dy + dz * dz);
                float v  = 17.0f - 5.0f * fabsf(d - r0);
                if (v > 2.0f) setPx(x, y, z, (uint8_t)v);
            }
}

/* ============================== 动画调度 ================================ */
static uint8_t  g_mode     = 0;
static uint32_t g_lastAnim = 0;
static const uint8_t MODE_CNT = 7;

static void updateAnimation(uint32_t t)
{
    clearLum();
    switch (g_mode) {
    case 0: animRain(t);                       break;
    case 1: animSphere(t);                     break;
    case 2: animSweep(t);                      break;
    case 3: animTwinkle(t);                    break;
    case 4: animCubeFrame();                   break;
    case 5: animWave(t);                       break;
    case 6: animGradient(t);                   break;
    default: g_mode = 0;                       break;
    }
}

/* ============================== 逐点自检 ================================ */
/* 串口输入 t：按 z→x→y 顺序逐个点亮，用来找出坏灯 / 接错线。
 * 216 个点 × 120ms ≈ 26 秒走完一遍。 */
static void runSelfTest(void)
{
    Serial.printf("[自检] 开始，逐点点亮 %d 个 LED…\n", BOX);
    for (int z = 0; z < N; ++z)
        for (int x = 0; x < N; ++x)
            for (int y = 0; y < N; ++y) {
                clearLum();
                setPx(x, y, z, 15);
                uint32_t t0 = millis();
                while (millis() - t0 < 120) renderFrame();
                Serial.printf("[自检] z=%d x=%d y=%d\n", z, x, y);
            }
    Serial.println(F("[自检] 完成"));
}

/* ============================== 串口命令 ================================ */
static void printHelp(void)
{
    Serial.println(F(
        "\n===== 6x6x6 LED Cube (4-bit gray) =====\n"
        " 1~7 : 切换动画 (雨滴/球壳/扫描/星光/边框/水波/渐变)\n"
        " n   : 下一个动画\n"
        " t   : 逐点自检\n"
        " s   : 显示一帧测试图（全部最亮）\n"
        " d   : 灰度阶梯测试（直接数 16 级）\n"
        " h   : 打印本帮助\n"
        "=======================================\n"));
}

static void plotAll(void)
{
    memset(lum, 15, sizeof(lum));
}

/* 灰度测试：6 层 × 每层 3 档，覆盖 0..15 级 */
static void plotGrayRamp(void)
{
    clearLum();
    for (int z = 0; z < N; ++z)
        for (int x = 0; x < N; ++x)
            for (int y = 0; y < N; ++y) {
                int v = z * 3 + (x % 3);        /* 0..17，超过 15 自动截断 */
                setPx(x, y, z, (uint8_t)v);
            }
}

static bool g_holdFrame = false;   /* true 时停住动画，只显示当前画面 */

static void handleSerial(void)
{
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c >= '1' && c <= '7') {
            g_mode = (uint8_t)(c - '1');
            g_holdFrame = false;
            Serial.printf("[模式] %d\n", g_mode + 1);
        } else if (c == 'n') {
            g_mode = (uint8_t)((g_mode + 1) % MODE_CNT);
            g_holdFrame = false;
            Serial.printf("[模式] %d\n", g_mode + 1);
        } else if (c == 't') {
            runSelfTest();
        } else if (c == 's') {
            g_holdFrame = true;
            plotAll();
            Serial.println(F("[测试] 全部最亮"));
        } else if (c == 'd') {
            g_holdFrame = true;
            plotGrayRamp();
            Serial.println(F("[测试] 灰度阶梯：z 越高越亮，x%3 再加一级"));
        } else if (c == '0') {
            g_holdFrame = false; clearLum();
        } else if (c == 'h') {
            printHelp();
        }
    }
}

/* ============================== 初始化 ================================== */
void setup(void)
{
    Serial.begin(115200);
    delay(200);
    Serial.println(F("\n6x6x6 LED Cube · ESP32 · 4-bit grayscale"));
    printHelp();

    pinMode(PIN_DATA,  OUTPUT);
    pinMode(PIN_CLK,   OUTPUT);
    pinMode(PIN_LATCH, OUTPUT);
    pinMode(PIN_SRCLR, OUTPUT);
    pinMode(PIN_OE,    OUTPUT);

    /* --- 上电安全顺序 --- */
    digitalWrite(PIN_OE,    HIGH);      /* 输出高阻 */
    digitalWrite(PIN_SRCLR, LOW);       /* 移位寄存器清零 */
    digitalWrite(PIN_LATCH, LOW);
    digitalWrite(PIN_LATCH, HIGH);      /* 把 0 锁存到输出寄存器 */
    digitalWrite(PIN_LATCH, LOW);
    digitalWrite(PIN_SRCLR, HIGH);      /* 释放清零 */

    for (int i = 0; i < N + 1; ++i) shiftByte(0x00);   /* 56 bit 全 0 */
    latchPulse();
    digitalWrite(PIN_OE, LOW);          /* 使能输出：全灭 */

    memset(rainZ, 0xFF, sizeof(rainZ));
    clearLum();
    randomSeed((uint32_t)micros());

    measurePlaneTime();
    Serial.printf("[时序] 单个子场开销 %u us，单位 %u us，整帧约 %u us\n",
                  (unsigned)g_planeUs, (unsigned)UNIT_US,
                  (unsigned)(N * GRAY_LEVELS * UNIT_US));

    g_lastAnim = millis();
}

/* ============================== 主循环 ================================== */
void loop(void)
{
    handleSerial();

    uint32_t t = millis();
    if (!g_holdFrame && t - g_lastAnim >= 40) {
        g_lastAnim = t;
        updateAnimation(t);
    }

    renderFrame();                      /* 约 5ms，200Hz 刷新 */
}
