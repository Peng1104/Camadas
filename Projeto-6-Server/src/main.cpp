#include <Arduino.h>

// Constants
const int INPUT_PIN = 6;                  // Digital pin that emulates the Tx pin
const int BAUD_RATE = 9600;               // Chose any baud rate you want
const long CPU_CLOCK = 21000000;          // The arduino cpu clock, 21 MHz
const long DELAY = CPU_CLOCK / BAUD_RATE; // Delay in milliseconds

void setup()
{
  Serial.begin(9600);
  pinMode(INPUT_PIN, INPUT); // Sets the digital pin as an output to emulate the Rx pin
}

void for_delay(double mult)
{
  for (int i = 0; mult * DELAY > i; i++)
  {
    asm("nop");
  }
}

char receiveData()
{
  // Looping until the start bit is received
  while (digitalRead(INPUT_PIN) == HIGH)
  {
  }
  for_delay(1.5); // Delay for 1.5 bits

  // Data bits
  char data = 0;
  int counter = 0;

  for (byte mask = 0x01; mask != 0; mask <<= 1)
  {
    if (digitalRead(INPUT_PIN) == HIGH)
    {
      data |= mask;
      counter++;
    }
    for_delay(1);
  }

  // Parity bit
  if (digitalRead(INPUT_PIN) == HIGH && counter % 2 == 0)
  {
    Serial.println("Parity error");
  }
  for_delay(1);

  // Stop bit
  if (digitalRead(INPUT_PIN) == HIGH)
  {
    return data;
  }
  return (char) 0;
}

void loop()
{
  int data = receiveData();
  
  if (data > 0) {
    Serial.println((char) data);
  }
}