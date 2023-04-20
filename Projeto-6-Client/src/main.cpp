#include <Arduino.h>

// Constants
const int OUTPUT_PIN = 5;         // Digital pin that emulates the Tx pin
const int BAUD_RATE = 9600;       // Chose any baud rate you want
const long CPU_CLOCK = 21000000; // The arduino cpu clock, 21 MHz
const long DELAY = CPU_CLOCK/BAUD_RATE;  // Delay in milliseconds

void setup()
{
  pinMode(OUTPUT_PIN, OUTPUT);    // Sets the digital pin as an output to emulate the Tx pin
  digitalWrite(OUTPUT_PIN, HIGH); // Sets the starting value of the digital pin to HIGH
}

void for_delay(double mult)
{
  for (int i = 0; mult * DELAY > i; i++)
  {
    asm("nop");
  }
}

void sendSerialByte(char data)
{
  // Start bit
  digitalWrite(OUTPUT_PIN, LOW);

  for_delay(1);

  // Data bits
  int counter = 0;

  for (byte mask = 0x01; mask != 0; mask <<= 1)
  {
    if (data & mask)
    {
      digitalWrite(OUTPUT_PIN, HIGH);
      counter++;
    }
    else
    {
      digitalWrite(OUTPUT_PIN, LOW);
    }
    for_delay(1);
  }

  // Parity bit
  if (counter % 2 == 0)
  {
    digitalWrite(OUTPUT_PIN, LOW); // Even parity
    for_delay(1);
  }
  else
  {
    digitalWrite(OUTPUT_PIN, HIGH); // Odd parity
    for_delay(1);
  }

  // Stop bit
  digitalWrite(OUTPUT_PIN, HIGH);
  for_delay(1);
}

void loop()
{
  sendSerialByte('P'); // Send the ASCIIletter each 2 seconds
  delay(2000); 
}