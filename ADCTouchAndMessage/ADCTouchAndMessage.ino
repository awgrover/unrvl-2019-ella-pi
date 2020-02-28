/*
  Test for A0..A5, plot them, with a "detect touch"

  On the "tiny"< only A0..A3=int 0...3 = digital 5,2,4,3

  Very clean +-5, prop response.
  90/4 =~ 22ms each
  134/5 =~ 26ms eachard

  Test setup
    3 actual wires
      foll covered pill bottle
      stainless press pot
      alum beer can
      ~620 "base" (prop to length)
      ~900 touch
      ~700 w/1 layer tape
      about 2 inch range to start detect
    No wire: ~400, almost insensitive

*/
#include <ADCTouch.h>

template <typename T, unsigned S> inline unsigned arraysize(const T (&v)[S]) {
  return S;
};

struct Touch {
  const int pin; // an A0.. up to A3
  int ref;  // do x.read(500);a x.ref=x.value;  to get a reference base
  int value;
  boolean last_state;

  void read(int tries = 100) {
    // sets .value
    this->value = ADCTouch.read(pin, tries);
  }
  boolean touched(float of_remaining = 0.25) {
    // empirically, a touch is about 1/4 of the remaining "head space" to 1024
    return (1024 - ref) * of_remaining < (value - ref);
  }
  char direction(float of_remaining = 0.25) {
    // give '+' or '-' or null to reflect the touched/untouched state
    if (touched(of_remaining) != last_state) {
      last_state = ! last_state;
      return last_state ? '+' : '-';
    }
    return (char) 0;
  }
};
Touch Touches[] = {{A0}, {A1}, {A2}, {A3}, {A4}, {A5}};

void setup()
{
  // No pins to setup, pins can still be used regularly, although it will affect readings

  Serial.begin(115200);
  Serial.println("start"); // our python code looks for this

  // header
  Serial.print("time"); Serial.print(": ");
  for (Touch &atouch : Touches) {
    Serial.print("pin"); Serial.print(atouch.pin); Serial.print(": ");
    Serial.print("value"); Serial.print(": ");
    Serial.print("+touch"); Serial.print(": ");
  }
  Serial.println();

  for (Touch &atouch : Touches) {
    atouch.read(500);
    atouch.ref = atouch.value;
    //Serial.print((long) &atouch); Serial.print(" ");
    Serial.print(atouch.pin); Serial.print(" ");
    Serial.print(atouch.ref); Serial.print(" ");
    Serial.println();
  }
  Touch &atouch = Touches[1];
  /*
    Serial.print("x "); Serial.print(atouch.pin); Serial.print(" ");
    Serial.print(atouch.ref); Serial.print(" ");
    Serial.print(atouch.value); Serial.print(" ");
    Serial.println();
  */
}

void loop()
{
  unsigned long last_hello = millis();
  if (millis() - last_hello > 4000) {
    Serial.println("start"); // some weirdness with python not resetting serial port on open
    last_hello = millis();
  }
  
  unsigned long start = micros();

  for (Touch &atouch : Touches) {
    atouch.read(100);
  }

  /*
  // how long to read pins, in micros * 10
  unsigned long delta = micros() - start;
  Serial.print(delta / 100); Serial.print(" ");
  */

  //value0 -= ref0;       //remove offset
  //value1 -= ref1;

  for (Touch &atouch : Touches) {
    char direction = atouch.direction();
    if (direction) {
      Serial.print(direction);
      Serial.print( atouch.pin - A0 ); // offset from 0
      Serial.println();

    }
    /*
      //Serial.print((long) &atouch); Serial.print("] ");
      Serial.print(atouch.ref); Serial.print(" ");
      Serial.print(atouch.value); Serial.print(" ");
      Serial.print(atouch.touched() * 20 + atouch.ref); Serial.print(" ");
      //break;
    */
  }


  //Serial.println();
  //delay(100);
}
