#include <Arduino.h>
#define TX_PIN 5
#define BAUD_RATE 9600
#define BIT_PERIOD (1000000 / BAUD_RATE)

volatile uint8_t bitToSend = 0;
volatile uint8_t byteToSend = 'A';
volatile bool transmissionInProgress = false;
volatile uint8_t numberOfOnes = 0;

void setup() {
  Serial.begin(9600);
  pinMode(TX_PIN, OUTPUT);
  digitalWrite(TX_PIN, HIGH);

  // Configure Timer1 for CTC (Clear Timer on Compare) mode and enable interrupt on OCR1A match
  TCCR1A = 0;
  TCCR1B = (1 << WGM12) | (1 << CS11); // Set CTC mode, prescaler = 8
  TIMSK1 = (1 << OCIE1A); // Enable compare match interrupt for OCR1A

  // Calculate and set the OCR1A value based on the desired baud rate
  OCR1A = (F_CPU / 8) / BAUD_RATE - 1;
  delay(1000);
}

void sendStartBit() {
  Serial.println("Sending start bit");
  digitalWrite(TX_PIN, LOW);
  TCNT1 = 0; // Reset Timer1 counter
  TIFR1 |= (1 << OCF1A); // Clear the interrupt flag
  sei(); // Enable global interrupts
}

void sendStopBit() {
  Serial.println("Sending stop bit");
  digitalWrite(TX_PIN, HIGH);
  transmissionInProgress = false;
}

void sendParityBit() {
  if (numberOfOnes % 2 == 0) {
    digitalWrite(TX_PIN, LOW);
  } else {
    digitalWrite(TX_PIN, HIGH);
  }
}

void loop() {
  delay(1000);
  if (!transmissionInProgress) {
    transmissionInProgress = true;
    bitToSend = 0;
    byteToSend = 'A';
    sendStartBit();
  }
}

ISR(TIMER1_COMPA_vect) {
  if (bitToSend == 0) {
    // Start bit has been sent, proceed with the data bits
    TCNT1 = 0; // Reset Timer1 counter
  } else if (bitToSend >= 1 && bitToSend <= 8) {
    // Send the current data bit
    if (byteToSend & (1 << (bitToSend - 1))) {
      digitalWrite(TX_PIN, HIGH);
      numberOfOnes++;
    } else {
      digitalWrite(TX_PIN, LOW);
    }
    TCNT1 = 0; // Reset Timer1 counter
  } else if (bitToSend == 9) {
    // Send parity bit
    sendParityBit();
    TCNT1 = 0; // Reset Timer1 counter
  } else if (bitToSend == 10) {
    // Send stop bit
    sendStopBit();
    cli(); // Disable global interrupts
  }
  bitToSend++;
}