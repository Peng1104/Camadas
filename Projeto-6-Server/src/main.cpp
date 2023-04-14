#include <Arduino.h>
#define RX_PIN 5
#define BAUD_RATE 9600
#define BIT_PERIOD (1000000 / BAUD_RATE)

volatile uint8_t bitToRead = 0;
volatile uint8_t receivedByte = 0;
volatile uint8_t parityBit = 0;
volatile bool receptionInProgress = false;
volatile bool isValid = true;

void startReception() {
  if (!receptionInProgress) {
    receptionInProgress = true;
    bitToRead = 0;
    TCNT1 = 0; // Reset Timer1 counter
    TIFR1 |= (1 << OCF1A); // Clear the interrupt flag
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(RX_PIN, INPUT);
  
  // Configure Timer1 for CTC (Clear Timer on Compare) mode and enable interrupt on OCR1A match
  TCCR1A = 0;
  TCCR1B = (1 << WGM12) | (1 << CS11); // Set CTC mode, prescaler = 8
  TIMSK1 = (1 << OCIE1A); // Enable compare match interrupt for OCR1A

  // Calculate and set the OCR1A value based on the desired baud rate
  OCR1A = (F_CPU / 8) / BAUD_RATE - 1;
  
  attachInterrupt(digitalPinToInterrupt(RX_PIN), startReception, FALLING);
  sei(); // Enable global interrupts
}

void loop() {
  if (receptionInProgress) {
    if (bitToRead == 10) {
      // Reception completed
      receptionInProgress = false;
      if (!isValid) {
        // The received byte is unvalid
        Serial.println("Invalid byte received");
      }
      Serial.print("Received byte: " + String(receivedByte));
      receivedByte = 0;
      bitToRead = 0;
      parityBit = 0;
    }
  }
}

ISR(TIMER1_COMPA_vect) {
  if (receptionInProgress) {
    if (bitToRead >= 1 && bitToRead <= 8) {
      // Read the current data bit
      if (digitalRead(RX_PIN)) {
        receivedByte |= (1 << (bitToRead - 1));
        parityBit++;
      }
    } else if (bitToRead == 9) {
      // Read the parity bit
      if (digitalRead(RX_PIN) && (parityBit % 2 == 0)) {
        isValid = false;
      }
    }
    bitToRead++;

    TCNT1 = 0; // Reset Timer1 counter
  }
}