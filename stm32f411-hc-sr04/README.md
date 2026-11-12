# HC-SR04 — TRIG 펄스 실습 (STM32F411RE)

**실습일:** 2026-11-12  
**보드:** NUCLEO-F411RE (STM32F411RETx)  
**개발 환경:** STM32CubeMX · STM32CubeIDE · Tektronix 오실로스코프

교수님 [F103RB HC-SR04 실습](https://github.com/gotree94/STM32/tree/main/NUCLEO_F103RB/06.HC-SR04)을 참고하되, **내가 실제 사용한 보드는 STM32F411RE**다. **오전 실습에서는** TRIG 신호 생성과 오실로스코프 파형 관찰까지 진행했다. **ECHO 수신과 거리 측정은 같은 날 오후 수업에서 진행하기로 했다.** 본인 실습 화면에서 필요한 사진 **7장**을 선별해 아래에 직접 첨부했다. 이 기록에 첨부된 사진에는 ECHO 거리 측정 완료 결과가 아직 없다.

## 1. STM32CubeMX 설정

![PA0 TRIGER1, TIM1 Prescaler 84-1](images/01_cubemx_gpio_tim1.webp)

- **PA0:** `TRIGER1`이라는 GPIO Output 이름으로 설정된 화면
- **TIM1:** Internal Clock, Prescaler `84-1`, Auto Reload `65535`

![클록 84MHz 설정](images/02_cubemx_clock_84mhz.webp)

- **SYSCLK / HCLK:** 84 MHz
- **APB1 PCLK1:** 42 MHz
- **APB2 PCLK2 / Timer Clock:** 84 MHz

TIM1 카운터는 **84 MHz ÷ 84 = 1 MHz**로 동작하도록 설정했으므로, 카운터 1이 증가하는 시간은 약 **1 µs**다.

## 2. 작성한 코드

### 타이머 시작과 마이크로초 단위 지연

![timer_start 및 delay_us 함수가 보이는 코드](images/03_delay_us_timer_code.webp)

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

### TRIG 펄스 출력

![trig 함수와 주석 처리된 echo 함수](images/04_trig_function_code.webp)

```c
void trig(void)
{
    HAL_GPIO_WritePin(TRIGER1_GPIO_Port, TRIGER1_Pin, HIGH);
    delay_us(10);
    HAL_GPIO_WritePin(TRIGER1_GPIO_Port, TRIGER1_Pin, LOW);
}
```

TRIG를 High로 만든 다음 `delay_us(10)`을 실행하고 Low로 복귀시킨다. 함수 실행 오버헤드가 있으므로 정확한 펄스 폭은 계측값으로 확인해야 한다.

### 메인 반복문

![timer_start, trig 및 delay_us 호출](images/05_main_loop_code.webp)

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

`delay_us(200)`은 **TRIG 펄스를 낸 뒤** 실행되는 코드상의 지연이다. 펄스 폭 10 µs와 지연 200 µs를 합하면 반복 주기는 약 210 µs 이상이 된다. 실제 주기는 함수 실행시간 등으로 달라질 수 있다.

## 3. HAL 함수 사용 및 확인

**HAL(Hardware Abstraction Layer)**은 STM32의 GPIO, 타이머, UART 같은 하드웨어를 C 함수로 제어할 수 있게 해주는 라이브러리다. 이번에 촬영한 `main.c`에는 HAL 함수를 사용한 코드가 확인된다.

| 사진에서 확인한 함수 | 이번 코드에서 한 역할 |
|---|---|
| `HAL_Init()` | 프로그램 시작 시 HAL 초기화 |
| `HAL_TIM_Base_Start(&htim1)` | TIM1 카운터 동작 시작 |
| `HAL_GPIO_WritePin(..., HIGH)` | TRIG 핀을 High로 설정 |
| `HAL_GPIO_WritePin(..., LOW)` | TRIG 핀을 Low로 설정 |
| `HAL_UART_Transmit(&huart2, ...)` | `printf` 문자 출력을 USART2로 보내도록 연결한 코드 |

특히 **`delay_us()`는 HAL에서 제공하는 `HAL_Delay()`와 다른, TIM1 카운터를 이용해 작성한 사용자 함수**다. 이 함수 내부에서는 `__HAL_TIM_SET_COUNTER()`와 `__HAL_TIM_GET_COUNTER()` 매크로를 사용한다.

```c
// main.c에서 촬영된 코드
trig();
// HAL_Delay(1);  // 주석 처리됨: 실행하지 않음
delay_us(200);    // 실제 호출한 사용자 지연 함수
```

따라서 이번 실습에서 `HAL_Delay(1)`을 실행했다고 쓰면 안 된다. **HAL로 GPIO와 TIM1을 제어하면서, 타이머 카운터를 이용한 마이크로초 지연 함수를 함께 사용했다.** USART2 전송 코드는 보이지만 시리얼 터미널에서 실제 문자가 수신된 결과까지 확인한 것은 아니다.

## 4. 오실로스코프 사진

### 약 4.8 kHz의 반복 펄스

![약 4.8kHz 반복 펄스](images/06_scope_4p8khz_repeat.webp)

화면에는 CH2의 **100 µs/div** 시간축과 반복되는 좁은 펄스가 보인다. 우측 아래의 표시 주파수는 약 **4.8 kHz**다. 이는 약 200 µs 지연을 반복하는 코드와 규모가 비슷하다. 프로브가 연결된 핀은 사진으로만 식별되지 않아 **TRIG 핀을 측정했다는 것은 별도로 확인이 필요**하다.

### 펄스 한 개 확대

![약 10µs폭 펄스](images/07_scope_10us_pulse.webp)

CH2 **10.0 µs/div** 화면에서 짧은 High 펄스가 관찰된다. 10 µs 수준의 펄스로 보이지만 사진에 표시된 정확한 펄스 폭 측정값은 없으므로 확정 숫자로 기록하지 않는다.

## 5. 오전 진행 내용과 오후 실습 계획

**완료:** F411RE CubeMX 설정, TIM1 1 µs 분주, `timer_start()`·`delay_us()`·`trig()` 작성, 반복 펄스 및 단일 펄스 파형 촬영.

**오후 실습 예정:** 오전 코드 사진에서 `echo()` 함수는 주석 처리돼 있다. 교수님 말씀에 따라 오후에는 ECHO 수신 핀 확인, 반사 시간 측정, 거리 계산 및 출력 과정을 배울 예정이다. 실제 수행 결과는 오후 실습 사진이나 코드가 확인된 뒤에 추가한다.

**참고:** 교수님 [HC-SR04 F103RB 예제](https://github.com/gotree94/STM32/tree/main/NUCLEO_F103RB/06.HC-SR04)에는 ECHO 처리 및 거리 계산이 나오지만, **오전 촬영 자료만으로는 이 단계의 완료를 확인할 수 없다.** F103RB 설정값을 F411RE 설정값으로 그대로 옮기지 않았다.

*사진 출처: 본인이 촬영해 제공한 화면. GitHub 표시를 위해 WebP 형식으로 용량을 줄였으며, 원본의 측정값이나 코드 내용을 임의로 변경하지 않았다.*
