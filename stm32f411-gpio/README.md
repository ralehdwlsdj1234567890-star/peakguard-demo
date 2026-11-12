# GPIO — STM32F411 실습 기록

**실습일:** 2026년 11월 11일  
**실습 환경:** STM32CubeIDE · STM32F411 계열 보드 · Tektronix TDS 2012B

이번에는 **PA5에 연결된 LD2 LED 토글**과 **PA6 GPIO 핀의 출력 설정 확인**을 구분해 정리했다. STM32CubeIDE에서 작성한 코드, 직접 촬영한 레지스터 화면, 오실로스코프 파형을 기록했다.

- [STM32F411xC/E 데이터시트](https://www.st.com/resource/en/datasheet/stm32f411ce.pdf)
- [RM0383 레퍼런스 매뉴얼](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
- [교수님 원본 GPIO_DOC](https://github.com/gotree94/STM32/tree/main/NUCLEO_F411RE/GPIO_DOC)

## 목차

**직접 진행한 실습**

- [1. LED 토글 코드](#1-led-토글-코드)
- [2. GPIOA 레지스터 확인](#2-gpioa-레지스터-확인)
- [3. 오실로스코프 측정](#3-오실로스코프-측정)
- [4. 실습 결과 및 배운 점](#4-실습-결과-및-배운-점)

**교수님 자료에서 F411만 복습한 부분**

- [5.1 Architecture](#51-architecture)
- [5.2 CLOCK](#52-clock)
- [5.3 Memory Map](#53-memory-map)
- [5.4 GPIO Register](#54-gpio-register)
- [5.5 Test](#55-test)


## 1. LED 토글 코드

STM32CubeIDE의 `main.c`에서 `MX_GPIO_Init()` 호출 이후, 다음 반복문을 작성했다. `counter` 변수는 반복 횟수를 세기 위해 넣었다.

```c
int counter = 0;

while (1)
{
    counter++;
    HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);
    HAL_Delay(1000);
}
```

![직접 작성한 STM32CubeIDE LED 토글 코드](images/01_led_toggle_code.jpg)

- `HAL_GPIO_TogglePin()`은 지정한 GPIO 출력 상태를 반전한다.
- `HAL_Delay(1000)`은 약 1초 동안 대기한다.
- 코드를 기준으로 출력이 약 1초마다 바뀌며, High와 Low가 한 번씩 반복되는 **한 주기는 약 2초**로 예상된다.

화면에서 주석 처리된 `HAL_GPIO_WritePin()`은 실행 중인 코드가 아니다. 이번 실습에 사용한 함수는 `HAL_GPIO_TogglePin()`이다.

## 2. GPIOA 레지스터 확인

STM32CubeIDE의 **Expressions** 창에서 `GPIOA`를 펼쳐 레지스터 값을 확인했다.

![직접 촬영한 GPIOA Expressions 창](images/02_gpioa_register_debug.jpg)

| 화면에서 확인한 항목 | 값 또는 의미 |
|---|---|
| GPIOA 시작 주소 | `0x40020000` |
| `MODER` | `0xA80010A0` — 핀 모드 설정 |
| `OTYPER` | `0x00000000` — 출력 방식 설정 |
| `ODR` | `0x00000000` — 촬영 시점의 출력 데이터 |
| `IDR` | `0x0000C00C` — 촬영 시점의 입력 상태 |

`MODER`는 각 핀당 2비트를 사용한다. 화면의 `0xA80010A0`을 해석하면 이 시점에서 **PA5는 입력(`00`), PA6은 출력(`01`)**으로 읽힌다.

코드에는 `LD2_Pin`이라는 이름이 사용되지만, 사진에는 해당 매크로가 실제로 어느 핀을 가리키는지 나와 있지 않다. 따라서 이 레지스터 캡처와 LED가 동작한 시점이 일치하는지는 추가로 확인해야 한다.

### 실습 구분: PA5는 LED, PA6은 외부 GPIO 핀

- **PA5 — LD2 LED:** NUCLEO-F411RE에서는 PA5가 보드 내장 LED(LD2)에 연결된다. 위 `HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin)` 코드는 LED를 토글하기 위해 작성한 코드다.
- **PA6 — 외부 핀:** PA6은 별도의 GPIO 핀(Arduino D12)이다. 위 디버거 사진은 `MODER = 0xA80010A0`으로, **PA6이 출력 모드(`01`)**로 설정된 상태를 보여 준다. PA6을 내장 LED라고 설명하면 안 된다.

즉, **PA5 LED 토글**과 **PA6 핀 레지스터 확인**은 서로 구분해 기록한다. 디버거 화면에서는 PA5가 입력 모드로 읽히므로, 그 화면을 PA5 LED 토글의 레지스터 검증 사진으로 사용하지 않는다.

| 핀 | 출력 모드 설정에 쓰는 MODER 비트 | ODR 출력 High 비트 |
|---|---|---|
| PA5 | `MODER[11:10] = 01` → `0x00000400` | `0x20` |
| PA6 | `MODER[13:12] = 01` → `0x00001000` | `0x40` |

위 표의 비트값은 레지스터 비트 위치를 이해하기 위한 계산이다. PA6 출력 모드는 위 디버거 캡처에서 확인되지만, **PA6 핀의 전압을 몇 V로 측정했는지**는 이 사진으로 확정할 수 없다. `LD2_Pin`과 `MX_GPIO_Init()` 원본을 확인하면 PA5 LED 초기화 설정도 정확히 기록할 수 있다.

## 3. 오실로스코프 측정

Tektronix TDS 2012B의 CH2를 이용해 신호가 바뀌는 두 순간을 촬영했다.

**상승 에지 — Low에서 High로 변경**

![직접 촬영한 상승 에지](images/03_oscilloscope_rising.jpg)

**하강 에지 — High에서 Low로 변경**

![직접 촬영한 하강 에지](images/04_oscilloscope_falling.jpg)

사진에는 수직 눈금 **1.00 V/div**, 시간 눈금 **10.0 ms/div**가 표시되어 있다. 각각의 사진에서 상승·하강 에지를 확인할 수 있었다.

다만 사진에는 한 번의 에지만 나타나므로 **1초 간격과 전체 2초 주기를 직접 측정한 결과는 아니다.** 주기를 정확히 측정하려면 시간축을 길게 설정해 연속된 에지를 한 화면에 표시해야 한다.

## 4. 실습 결과 및 배운 점

GPIO 제어 코드를 실행하면 마이크로컨트롤러의 출력 핀 상태가 바뀌고, 오실로스코프로 전압 변화를 관찰할 수 있다는 것을 배웠다. 디버거에서는 GPIOA의 시작 주소와 레지스터 값을 확인했다.

또한 LED 토글 코드를 작성하는 것과 레지스터 값으로 동작을 검증하는 것은 별개라는 점을 알게 됐다. 다음에는 `main.h`의 `LD2_Pin` 정의와 `MX_GPIO_Init()`의 핀 설정을 비교하고, 실제 출력 주기를 측정해 보고 싶다.

**다음 확인 항목**

- [ ] `LD2_Pin`의 실제 포트·핀 번호 확인
- [ ] GPIO 초기화 이후 `MODER` 값 확인
- [ ] 연속 파형으로 출력 주기·주파수 직접 측정

---

## 5. 교수님 GPIO_DOC 복습 — STM32F411만

아래 5개 접기식 항목은 교수님 [GPIO_DOC](https://github.com/gotree94/STM32/tree/main/NUCLEO_F411RE/GPIO_DOC)의 F411 설명과 그림을 참고해 복습한 내용이다. 이 그림들은 교수님 수업 자료이며, 직접 수행하고 촬영한 실습은 위 1~4절에 따로 기록했다.

### 5.1 Architecture

<details>
<summary><strong>Architecture — STM32F411 (그림 2장)</strong></summary>

Cortex-M4는 코드를 실행하고, AHB 버스를 통해 GPIO와 같은 주변장치 레지스터에 접근한다. STM32F411에서 GPIO는 AHB1 쪽에 연결된다.

**시스템 버스 구조**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/arm-arch-2.png" alt="교수님 F411 자료: 시스템 버스 구조" width="760">

**Cortex-M4와 버스 연결**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/arm-arch-1.png" alt="교수님 F411 자료: Cortex-M4와 버스 연결" width="760">

</details>

### 5.2 CLOCK

<details>
<summary><strong>CLOCK — STM32F411 (그림 2장)</strong></summary>

GPIO를 사용하려면 먼저 RCC에서 해당 포트의 클록을 켜야 한다. `MX_GPIO_Init()` 코드에서 GPIOA 클록 활성화 부분을 확인할 수 있다.

**STM32F411 클록 구조 (1)**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/411-clk1.png" alt="교수님 F411 자료: STM32F411 클록 구조 (1)" width="760">

**STM32F411 클록 구조 (2)**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/411-clk2.png" alt="교수님 F411 자료: STM32F411 클록 구조 (2)" width="760">

</details>

### 5.3 Memory Map

<details>
<summary><strong>Memory Map — STM32F411 (그림 4장)</strong></summary>

GPIOA 레지스터는 `0x40020000`부터 시작한다. 예를 들어 `MODER`는 `+0x00`, `ODR`은 `+0x14`, `BSRR`은 `+0x18`에 있다.

**메모리 구조**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/007-1.png" alt="교수님 F411 자료: 메모리 구조" width="760">

**주변장치 주소**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/009-1.png" alt="교수님 F411 자료: 주변장치 주소" width="760">

**AHB 주소 영역**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/010-1.png" alt="교수님 F411 자료: AHB 주소 영역" width="760">

**GPIO 주소 확인**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/011-1.png" alt="교수님 F411 자료: GPIO 주소 확인" width="760">

</details>

### 5.4 GPIO Register

<details>
<summary><strong>GPIO — STM32F411 (그림 15장)</strong></summary>

GPIO 핀은 입력, 출력, 대체 기능, 아날로그 모드 중 하나로 설정한다. LED를 제어할 때는 출력 모드와 ODR·BSRR의 역할이 중요하다.

**GPIO 기본 구성**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F16.png" alt="교수님 F411 자료: GPIO 기본 구성" width="760">

**입력 모드**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F18.png" alt="교수님 F411 자료: 입력 모드" width="760">

**출력 모드**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F19.png" alt="교수님 F411 자료: 출력 모드" width="760">

**대체 기능**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F20.png" alt="교수님 F411 자료: 대체 기능" width="760">

**아날로그 모드**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F21.png" alt="교수님 F411 자료: 아날로그 모드" width="760">

**MODER 비트**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/841.png" alt="교수님 F411 자료: MODER 비트" width="760">

**레지스터 842**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/842.png" alt="교수님 F411 자료: 레지스터 842" width="760">

**레지스터 843**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/843.png" alt="교수님 F411 자료: 레지스터 843" width="760">

**레지스터 844**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/844.png" alt="교수님 F411 자료: 레지스터 844" width="760">

**레지스터 845**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/845.png" alt="교수님 F411 자료: 레지스터 845" width="760">

**레지스터 846**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/846.png" alt="교수님 F411 자료: 레지스터 846" width="760">

**레지스터 847**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/847.png" alt="교수님 F411 자료: 레지스터 847" width="760">

**레지스터 848**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/848.png" alt="교수님 F411 자료: 레지스터 848" width="760">

**레지스터 849**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/849.png" alt="교수님 F411 자료: 레지스터 849" width="760">

**AFR 비트**

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/8410.png" alt="교수님 F411 자료: AFR 비트" width="760">

</details>

### 5.5 Test — F411 디버깅 예제

<details>
<summary><strong>교수님 F411 Test 순서와 참고 화면 15장 펼치기</strong></summary>

이 부분은 [교수님 GPIO_DOC의 F411 Test](https://github.com/gotree94/STM32/tree/main/NUCLEO_F411RE/GPIO_DOC#4-test)를 복습하며 정리했다. **아래 15장은 교수님 원본 자료의 화면이며, 내가 직접 실행·촬영한 결과가 아니다.**

#### 먼저 알아둘 것

| 구분 | 뜻 | 디버깅할 때 확인하는 내용 |
|---|---|---|
| Expressions | 변수·포인터 값 관찰 | `LD2_GPIO_Port` |
| SFR | 주변장치 제어 레지스터 | `MODER`, `ODR`, `IDR`, `BSRR` |
| Core Registers | CPU 내부 레지스터 | `R0~R12`, `SP`, `LR`, `PC` |
| Disassembly | C 코드를 컴파일한 명령 확인 | 함수 호출과 메모리 쓰기 명령 |
| Memory | 주소의 실제 데이터 확인 | GPIOA 시작 주소 `0x40020000` |

STM32F411의 GPIOA는 `0x40020000`부터 시작한다. 따라서 `MODER`는 `+0x00`, `ODR`은 `+0x14`, `BSRR`은 `+0x18`이다. 교수님 예제의 `HAL_GPIO_WritePin()`은 **BSRR에 값을 써서** 핀을 설정하거나 해제하는 과정을 보여 준다.

#### 교수님 화면 순서

**1. Expressions에 `LD2_GPIO_Port` 추가**

LED 핀과 연결된 GPIO 포트 정보를 디버거에서 확인하는 방법.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_001.png" alt="교수님 F411 Test 참고자료: Expressions에 LD2_GPIO_Port 추가" width="760">

**2. SFR 창에서 GPIO 레지스터 확인**

`MODER`, `ODR`, `IDR`, `BSRR` 등 주변장치 레지스터를 확인.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_002.png" alt="교수님 F411 Test 참고자료: SFR 창에서 GPIO 레지스터 확인" width="760">

**3. Core Registers 확인**

CPU에서 사용하는 `R0~R12`, `SP`, `LR`, `PC` 확인.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_003.png" alt="교수님 F411 Test 참고자료: Core Registers 확인" width="760">

**4. Disassembly 창 열기**

교수님 자료의 `Window → Show View → Other → Disassembly` 메뉴.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_013.png" alt="교수님 F411 Test 참고자료: Disassembly 창 열기" width="760">

**5. Disassembly 화면 확인**

C 코드와 대응하는 어셈블리 명령을 살펴보는 화면.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_014.png" alt="교수님 F411 Test 참고자료: Disassembly 화면 확인" width="760">

**6. Cortex-M4 코어 레지스터 구성**

주변장치용 SFR과 CPU 코어 레지스터의 차이 이해.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_MCU_Core.png" alt="교수님 F411 Test 참고자료: Cortex-M4 코어 레지스터 구성" width="760">

**7. Memory 창에서 `0x40020000` 입력**

STM32F411 GPIOA의 시작 주소에서 레지스터 메모리를 확인.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_004.png" alt="교수님 F411 Test 참고자료: Memory 창에서 0x40020000 입력" width="760">

**8. `HAL_Init()` 단계**

HAL 초기화 위치를 확인하는 교수님 예제.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_005.png" alt="교수님 F411 Test 참고자료: HAL_Init() 단계" width="760">

**9. `SystemClock_Config()` 단계**

시스템 클록 설정 위치를 확인하는 교수님 예제.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_006.png" alt="교수님 F411 Test 참고자료: SystemClock_Config() 단계" width="760">

**10. `MX_GPIO_Init()` 단계**

GPIO 클록·핀 초기화가 수행되는 위치 확인.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_007.png" alt="교수님 F411 Test 참고자료: MX_GPIO_Init() 단계" width="760">

**11. `MX_USART2_UART_Init()` 단계**

교수님 프로젝트에 포함된 USART2 초기화 화면.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_008.png" alt="교수님 F411 Test 참고자료: MX_USART2_UART_Init() 단계" width="760">

**12. `HAL_GPIO_WritePin(..., 1)`**

교수님 예제의 LED 출력 High 설정.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_009.png" alt="교수님 F411 Test 참고자료: HAL_GPIO_WritePin(..., 1)" width="760">

**13. `HAL_Delay(1000)`**

출력 변경 후 1초 대기.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_010.png" alt="교수님 F411 Test 참고자료: HAL_Delay(1000)" width="760">

**14. `HAL_GPIO_WritePin(..., 0)`**

교수님 예제의 LED 출력 Low 설정.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_011.png" alt="교수님 F411 Test 참고자료: HAL_GPIO_WritePin(..., 0)" width="760">

**15. 두 번째 `HAL_Delay(1000)`**

다음 출력 변경 전 1초 대기.

<img src="https://raw.githubusercontent.com/gotree94/STM32/main/NUCLEO_F411RE/GPIO_DOC/img/F411_R_012.png" alt="교수님 F411 Test 참고자료: 두 번째 HAL_Delay(1000)" width="760">

#### 교수님 코드와 내가 작성한 코드의 차이

**교수님 F411 Test 예제**는 출력 값을 지정하는 `HAL_GPIO_WritePin()` 방식이다.

```c
HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, 1);
HAL_Delay(1000);
HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, 0);
HAL_Delay(1000);
```

**내가 작성한 실습 코드**는 현재 출력 상태를 반대로 바꾸는 `HAL_GPIO_TogglePin()` 방식이다.

```c
HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);
HAL_Delay(1000);
```

두 방식 모두 LED의 High/Low 출력을 바꿀 수 있지만, **서로 다른 함수와 실습 기록**이다. 위의 교수님 `WritePin` 코드, Core Registers, Disassembly 화면을 내가 직접 실행한 것처럼 기록하지 않는다.

#### 내가 확인한 화면과 추가로 확인할 내용

- **직접 확인:** LED 토글 코드, GPIOA Expressions 화면, 상승·하강 에지 사진(위 1~3절)
- **핀 구분:** PA5는 LD2 LED에 연결된 핀이고, PA6은 별도 외부 GPIO 핀. 디버거의 `MODER = 0xA80010A0`은 PA6 출력 설정이 보이는 화면이다
- **추가 확인:** `LD2_Pin` 정의, `MX_GPIO_Init()`에서 사용된 핀 설정, 실제 신호의 한 주기

</details>


## 참고자료 및 확인할 점

- [ST STM32F411xC/E 데이터시트](https://www.st.com/resource/en/datasheet/stm32f411ce.pdf)
- [ST RM0383 레퍼런스 매뉴얼](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
- [교수님 STM32F411 GPIO_DOC 원문](https://github.com/gotree94/STM32/tree/main/NUCLEO_F411RE/GPIO_DOC)
- [STM32F411 GPIO 정리 사례](https://github.com/yeooooly/STM32F411_Project/tree/main/01_GPIO_DOC) — PA5 토글 실습과 PA6 레지스터 실습을 나누어 정리하는 방식만 참고. 해당 저장소의 사진과 측정값을 본인 실습 결과로 사용하지 않음.

PA5는 LD2 LED 제어 핀이고 PA6은 별도로 확인한 GPIO 출력 핀이다. `MODER = 0xA80010A0`은 **PA6 출력 모드**를 보여 주는 화면이지 PA5 LED 출력 모드의 증거가 아니다. PA5에 사용된 `LD2_Pin` 매크로와 초기화 설정 원본은 추가 확인이 필요하다. 또한 오실로스코프 사진은 상승·하강 에지를 보여주지만 2초 주기 자체를 계측한 증거는 아니다.
