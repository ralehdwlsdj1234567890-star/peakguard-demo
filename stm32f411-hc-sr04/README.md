# STM32F411 — HC-SR04 TRIG 신호 실습 (2026-11-12)

STM32F411RE NUCLEO 보드에서 HC-SR04 초음파센서의 TRIG 펄스를 만드는 코드를 작성하고 오실로스코프로 신호를 관찰했다. 이 문서는 **직접 촬영한 화면에서 확인되는 내용만** 기록했다. ECHO를 이용한 거리 측정은 아직 완료된 것으로 기록하지 않는다.

## 1. 실습 환경과 CubeMX 설정

- 보드: **NUCLEO-F411RE / STM32F411RETx**
- 개발 도구: STM32CubeMX, STM32CubeIDE
- 계측기: Tektronix 오실로스코프
- CubeMX 화면: **PA0 = TRIGER1**, GPIO Output
- TIM1: Internal Clock, Prescaler **84-1**, Counter Period **65535**
- 클록 설정: SYSCLK/HCLK **84 MHz**, APB1 **42 MHz**, APB2 타이머 **84 MHz**

위 화면 설정대로라면 TIM1 카운터 주파수는 84 MHz / 84 = **1 MHz**이고, 카운터 1증가는 **1 μs**에 해당한다.

## 2. 직접 작성한 코드

### 변수 선언

```c
#define HIGH 1
#define LOW 0
long unsigned int echo_time;
int dist;
```

### TIM1 시작 및 마이크로초 지연

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

### TRIG 신호 출력

```c
void trig(void)
{
    HAL_GPIO_WritePin(TRIGER1_GPIO_Port, TRIGER1_Pin, HIGH);
    delay_us(10);
    HAL_GPIO_WritePin(TRIGER1_GPIO_Port, TRIGER1_Pin, LOW);
}
```

이 코드는 TRIG 핀을 High로 설정하고 약 10 μs 후 Low로 바꾸도록 작성한 것이다. 실제 펄스 폭을 10 μs로 측정했다는 뜻은 아니다.

### 초기화와 반복문

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

`delay_us(200)`은 코드상의 대기시간이다. 실제 반복 주기가 200 μs로 측정됐다고 단정할 수 없다. `printf` 출력은 UART2 전송 함수와 연결된 코드가 보인다.

**주의:** 사진에 보이는 `echo()` 함수는 주석 처리된 상태다. ECHO의 High 시간을 읽고 거리를 계산하는 기능이 실행됐다고 쓰지 않는다.

## 3. 오실로스코프 관찰

직접 촬영한 CH2 화면에서는 짧은 펄스가 반복되는 모습과 시간축을 바꾼 화면이 확인된다.

| 화면 | 사진에서 읽히는 정보 |
|---|---|
| 자동 측정 | 첨두치 **3.36 V**, 주기 **1.976 ms?**, 주파수 **506.1 Hz?**, 평균치 **30.6 mV** |
| 반복 펄스 | 100 μs/div 및 50 μs/div 시간축에서 좁은 펄스 반복 |
| 단일 펄스 | 10 ms/div 화면에서 짧은 High 구간 확인 |

측정 화면의 `?` 표시는 계측기가 표시한 그대로 남겼다. **CH2 프로브가 연결된 정확한 핀은 사진만으로 확정되지 않으므로**, 모든 파형을 TRIG 핀 측정값이라고 단정하지 않는다.

## 4. 오늘 확인한 것과 다음 확인 사항

- **확인:** PA0의 TRIGER1 GPIO 설정, TIM1·클록 설정 화면, TRIG 펄스 생성 코드, 오실로스코프 CH2 펄스 파형
- **추가 확인:** CH2 실제 측정 핀, TRIG 펄스 폭 커서 측정, 센서 권장 측정 간격, ECHO 입력 코드 및 거리 계산
- **사진:** 직접 촬영한 원본 **13장**은 별도 정리한 실습 사진 패키지에 보관했다. 이 저장소 폴더에는 아직 사진 파일을 업로드하지 않았으므로 이미지가 있는 것처럼 표시하지 않는다.

[이전 GPIO 실습](../stm32f411-gpio/README.md) · [교수님 STM32F411 GPIO_DOC](https://github.com/gotree94/STM32/tree/main/NUCLEO_F411RE/GPIO_DOC)
