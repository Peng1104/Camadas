#include <Arduino.h>

// Constants
const int digitalRxPin = 6; // Digital pin that emulates the Tx pin
const long baudRate = 9600;   // Chose any baud rate you want
const long bitDelay = 1000000L / baudRate; // Calculate the delay between bits

void setup() {
  Serial.begin(9600);
  pinMode(digitalRxPin, INPUT); // Sets the digital pin as an output to emulate the Rx pin
}

char receiveData() {
  // Looping until the start bit is received
  while (digitalRead(digitalRxPin) == HIGH) {
    delayMicroseconds(bitDelay);
  }

  // Data bits
  char data = 0;
  int numberOfOnes = 0;
  for (byte mask = 0x01; mask != 0; mask <<= 1) {
    delayMicroseconds(bitDelay);
    if (digitalRead(digitalRxPin) == HIGH) {
      data |= mask;
      numberOfOnes++; 
    }
  }

  // Parity bit
  delayMicroseconds(bitDelay);
  if (digitalRead(digitalRxPin) == HIGH && numberOfOnes % 2 == 0) {
    Serial.println("Parity error");
  }

  // Stop bit
  delayMicroseconds(bitDelay);
  if (digitalRead(digitalRxPin) == HIGH) {
    return data;
  }
  return 'e';
}

void loop() {
  char receivedByte = receiveData();
  if (receivedByte != 'e') {
    Serial.println(receivedByte);
  }
  delay(1000);
}

/* Ref: https://electronoobs.com/eng_arduino_tut140.php
Calculations for the timer: 
  System clock 16 Mhz and Prescalar 64;
  Timer 1 speed = 16Mhz/256 = 250 Khz    
  Pulse time = 1/250 Khz =  4us  
  Count up to = (1/bitDelay) / 4us = ?


void setup() {
  Serial.begin(9600);
  pinMode(digitalRxPin, INPUT); // Sets the digital pin as an output to emulate the Rx pin
  cli(); // Disable interrupts 
  TCCR1A = 0;                 
  TCCR1B = 0;                 
  TCCR1B |= B00000011;      
  TIMSK1 |= B00000010;
  OCR1A = bitDelay/4e-6;
  sei();  //allow interrupts        
}

void loop() {
....
}

ISR(TIMER1_COMPA_vect){
  TCNT1  = 0; //Reset the timer for next interrupt
  ...
}
*/ 