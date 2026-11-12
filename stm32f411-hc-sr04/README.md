# HC-SR04 — STM32F411RE TRIG 펄스 실습 (2026-11-12)

**환경:** NUCLEO-F411RE · STM32CubeMX / STM32CubeIDE · Tektronix 오실로스코프

교수님 [NUCLEO-F103RB HC-SR04 예제](https://github.com/gotree94/STM32/tree/main/NUCLEO_F103RB/06.HC-SR04)를 참고해 **STM32F411RE에서 실제로 진행한 단계까지만** 기록했다. 오늘은 TRIG 펄스 출력과 오실로스코프 파형 확인까지 진행했다. F103RB 예제 전체를 완료한 것은 아니다.

## 1. CubeMX 설정

| 항목 | 직접 촬영한 화면에서 확인한 설정 |
|---|---|
| MCU / 보드 | STM32F411RETx · NUCLEO-F411RE |
| PA0 | `TRIGER1` / GPIO_Output |
| TIM1 | Internal Clock, Prescaler `84-1`, Counter Period `65535` |
| SYSCLK / HCLK | 84 MHz |
| APB1 PCLK1 | 42 MHz |
| APB2 PCLK2 / TIM1 clock | 84 MHz |

따라서 TIM1은 **84 MHz ÷ 84 = 1 MHz**로 카운트한다. 카운터가 1 증가하는 시간은 이론적으로 **1 µs**다.

## 2. 작성한 코드

### TIM1 시작과 µs 지연

```c
void timer_start(void)
{
    HAL_TIM_Base_Start(&htim1);
}

void delay_us(uint16_t us)
{
    __HAL_TIM_SET_COUNTER(&htim1, 0);
    while (__HAL_TIM_GET_COUNTER(&htim1) < us);
}
```

### TRIG 출력

```c
void trig(void)
{
    HAL_GPIO_WritePin(TRIGER1_GPIO_Port, TRIGER1_Pin, HIGH);
    delay_us(10);
    HAL_GPIO_WritePin(TRIGER1_GPIO_Port, TRIGER1_Pin, LOW);
}
```

### main 반복문

```c
MX_GPIO_Init();
MX_TIM1_Init();
MX_USART2_UART_Init();
timer_start();
printf("Ranging with HC-SR04\n");

while (1)
{
    trig();
    // HAL_Delay(1);
    delay_us(200);
}
```

코드상 TRIG High 지연은 약 **10 µs**, 반복 사이 지연은 약 **200 µs**다. 실제 간격에는 함수 실행 오버헤드가 포함되므로 정확히 210 µs라고 단정하지 않는다.

## 3. 직접 찍은 오실로스코프 화면 해석

- 반복 펄스 화면: CH2, 시간축 **100 µs/div**, 표시 주파수 **약 4.8 kHz**. 약 200 µs 지연을 반복하는 코드와 대략 일치한다.
- 펄스 확대 화면: CH2, **10.0 µs/div**. 짧은 High 펄스가 보인다. **10 ms/div가 아니라 10 µs/div**이다.
- 앞서 촬영한 자동 측정 화면에는 **1.976 ms? / 506.1 Hz?**가 표시되어 있다. 뒤의 4.8 kHz 화면과 조건이 같다는 근거는 없으므로 같은 측정값으로 합치지 않는다.
- 프로브가 물린 **정확한 핀**은 사진만으로 확정할 수 없다. TRIG 핀의 직접 측정이라고 단정하지 않는다.

## 4. 실습 사진 선별

받은 화면 중 중복과 동일 파형의 배율만 다른 사진을 제외하고 **7장만** 기록용으로 선별했다.

| 기록용 파일명 | 내용 |
|---|---|
| `01_cubemx_gpio_tim1.jpg` | PA0 출력 · TIM1 분주 |
| `02_cubemx_clock_84mhz.jpg` | SYSCLK/HCLK 및 APB 클록 |
| `03_delay_us_timer_code.jpg` | `timer_start()` · `delay_us()` |
| `04_trig_function_code.jpg` | `trig()` 및 주석 처리된 `echo()` |
| `05_main_loop_code.jpg` | 초기화 · `trig()` · `delay_us(200)` |
| `06_scope_4p8khz_repeat.jpg` | 반복 펄스 |
| `07_scope_10us_pulse.jpg` | 단일 펄스 확대 |

**사진의 실제 파일 업로드는 아직 이 GitHub 경로에 반영되지 않았다.** 선별된 이미지 원본은 별도 업로드 패키지로 정리했다. 파일이 없는 상태에서 깨진 이미지 링크를 넣지 않았다.

## 5. 완료한 내용과 다음 단계

**현재까지 수행:** F411RE 핀·클록·타이머 설정, TIM1 기반 지연 함수, TRIG 출력 코드, CH2 펄스 사진 촬영.

**아직 미수행:** 사진에서 `echo()`는 주석 처리돼 있다. ECHO 시간 수신, 거리(mm/cm) 계산, 거리값 출력, 실측 거리 대조는 수행한 것으로 기록하지 않는다.

> 교수님 F103RB 예제의 ECHO 측정·거리 계산·Node.js 화면은 **학습 예정 참고자료**다. F411RE 실습을 완료했다고 표기하지 않는다.

[교수님 HC-SR04 실습](https://github.com/gotree94/STM32/tree/main/NUCLEO_F103RB/06.HC-SR04) · [전날 F411 GPIO 실습](../stm32f411-gpio/README.md)
