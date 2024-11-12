To set up an automatic watering system for your flowers using a Raspberry Pi and GPIO, here’s a step-by-step guide covering hardware requirements, wiring, and Python code for automation.

### 1. **Materials Needed**
   - Raspberry Pi (any model with GPIO pins, e.g., Raspberry Pi 3 or 4)
   - MicroSD card (with Raspberry Pi OS installed)
   - Soil moisture sensor module
   - Relay module (to control a water pump)
   - Small water pump (5V or 12V, matching your relay specifications)
   - Tubing (to carry water to your plants)
   - Jumper wires
   - Power supply (for the pump, if needed, depending on your model)

### 2. **Setting Up Hardware**
   - **Soil Moisture Sensor**: Connect the moisture sensor to your Raspberry Pi to detect soil dryness.
     - Connect the **VCC** of the sensor to **5V** on the Raspberry Pi.
     - Connect the **GND** to **GND**.
     - Connect the **Signal (OUT)** pin to **GPIO Pin 17** (you can change this in the code).
   
   - **Relay Module and Water Pump**: Use a relay module to control the pump.
     - Connect **VCC** on the relay to **5V**.
     - Connect **GND** to **GND**.
     - Connect the **IN** pin of the relay to **GPIO Pin 18** (adjustable in code).
     - Connect the **COM** and **NO** (Normally Open) terminals of the relay to the water pump’s power supply. This will allow the relay to control the pump by opening and closing the circuit.

   **Wiring Diagram**:
   ```
   Soil Moisture Sensor (VCC) ---> Raspberry Pi (5V)
   Soil Moisture Sensor (GND) ---> Raspberry Pi (GND)
   Soil Moisture Sensor (OUT) ---> Raspberry Pi (GPIO 17)
   
   Relay Module (VCC) ---> Raspberry Pi (5V)
   Relay Module (GND) ---> Raspberry Pi (GND)
   Relay Module (IN) ---> Raspberry Pi (GPIO 18)
   Relay NO & COM ---> Water Pump Power
   ```

### 3. **Install Necessary Libraries**
   Run these commands on your Raspberry Pi to install necessary libraries.
   ```bash
   sudo apt update
   sudo apt install python3-gpiozero python3-rpi.gpio
   ```

### 4. **Python Code for Automatic Watering**

   Create a Python script, for example `watering_system.py`, that reads the soil moisture level and activates the pump if the soil is too dry.

   ```python
   from gpiozero import DigitalOutputDevice, DigitalInputDevice
   from time import sleep

   # Define GPIO pins
   SOIL_MOISTURE_PIN = 17
   RELAY_PIN = 18

   # Initialize moisture sensor and relay
   soil_moisture_sensor = DigitalInputDevice(SOIL_MOISTURE_PIN)
   relay = DigitalOutputDevice(RELAY_PIN)

   # Define watering function
   def water_plants():
       print("Soil is dry, starting pump...")
       relay.on()
       sleep(5)  # Adjust time based on how much water your plants need
       relay.off()
       print("Stopping pump.")

   try:
       while True:
           if soil_moisture_sensor.value == 0:  # 0 means dry soil
               water_plants()
           else:
               print("Soil is moist, no need to water.")
           sleep(60)  # Check moisture level every 60 seconds
   except KeyboardInterrupt:
       print("Exiting program.")
   ```

### 5. **Run the Program**
   Run your Python script to start the automatic watering system.
   ```bash
   python3 watering_system.py
   ```

### 6. **Adjustments and Considerations**
   - **Watering Duration**: Adjust `sleep(5)` in the `water_plants()` function based on how much water is needed.
   - **Moisture Check Frequency**: You can change `sleep(60)` to increase or decrease the time between moisture checks.
   - **Water Supply**: Ensure you have enough water in your reservoir and that the pump can reach it.

With this setup, your Raspberry Pi will monitor soil moisture and automatically water your flowers when the soil is dry!
