import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(AlwaysSunnyApp());
}

class AlwaysSunnyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(
          title: const Text(
            'Always Sunny',
            style: TextStyle(
              color: Colors.white,
            ),
          ),
          backgroundColor: const Color.fromARGB(255, 30, 58, 101),
          centerTitle: true,
        ),
        body: SunnyDaysScreen(),
      ),
    );
  }
}

class SunnyDaysScreen extends StatefulWidget {
  @override
  _SunnyDaysScreenState createState() => _SunnyDaysScreenState();
}

class _SunnyDaysScreenState extends State<SunnyDaysScreen> {
  DateTime? startDate;
  DateTime? endDate;
  String city = '';
  String province = '';
  String sunnyScore = ''; // To hold the sunny score value

  //new variables for advanced details
  bool showAdvanced = false;
  String clearSkies = "";
  String windSpeed = "";
  String rainScore = "";
  String snowScore = "";

  // Updated function to fetch the sunny score from Flask backend
  Future<void> getSunnyScore() async {
    if (city.isEmpty || province.isEmpty || startDate == null || endDate == null) {
      return;
    }

    final url = Uri.parse('http://127.0.0.1:5000/get_sunny_score');
    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: json.encode({
        'city': city,
        'province': province,
        'start_date': startDate!.toString().split(' ')[0],
        'end_date': endDate!.toString().split(' ')[0],
      }),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      setState(() {
        sunnyScore = data['sunny_score'].toString();
        clearSkies = data['clear_skies'].toString();
        windSpeed = data['wind_speed'].toString();
        rainScore = data['rain_amount'].toString();
        snowScore = data['snow_amount'].toString();

      });
    } else {
      setState(() {
        sunnyScore = 'Error fetching score';
      });
    }
  }


  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color.fromARGB(255, 40, 70, 135),
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          const Icon(
            Icons.wb_sunny,
            color: Color.fromARGB(255, 235, 206, 14),
            size: 100,
          ),
          const SizedBox(height: 20),
          
          Row(
            children: [
              // TextField for province
              Expanded(
              child: TextField(
                onChanged: (value) {
                  setState(() {
                    city = value; // Update province when text changes
                  });
                },
                decoration: const InputDecoration(
                  hintText: 'Enter city name',
                  prefixIcon: Icon(Icons.search),
                  border: OutlineInputBorder(),
                  filled: true,
                  fillColor: Color.fromARGB(255, 200, 200, 200),
                ),
              ),
            ),
            const SizedBox(width: 1), // Add spacing between the TextFields
            // TextField for city
            Expanded(
            child: TextField(
              onChanged: (value) {
                setState(() {
                  province = value; // Update city when text changes
                });
              },
              decoration: const InputDecoration(
                hintText: 'Enter province/state name',
                
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Color.fromARGB(255, 200, 200, 200),
              ),
            ),
          ),
        ],
      ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              Expanded(
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color.fromARGB(255, 200, 200, 200),
                  ),
                  onPressed: () async {
                    DateTime? pickedDate = await showDatePicker(
                      context: context,
                      initialDate: DateTime.now(),
                      firstDate: DateTime(2000),
                      lastDate: DateTime(2100),
                    );
                    if (pickedDate != null && pickedDate != startDate) {
                      setState(() {
                        startDate = pickedDate;
                      });
                    }
                  },
                  child: Text(
                    startDate != null
                        ? 'Start: ${startDate!.toLocal().toString().split(' ')[0]}'
                        : 'Select Start Date',
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                      backgroundColor: const Color.fromARGB(255, 200, 200, 200)),
                  onPressed: () async {
                    DateTime? pickedDate = await showDatePicker(
                      context: context,
                      initialDate: DateTime.now(),
                      firstDate: DateTime(2000),
                      lastDate: DateTime(2100),
                    );
                    if (pickedDate != null && pickedDate != endDate) {
                      setState(() {
                        endDate = pickedDate;
                      });
                    }
                  },
                  child: Text(
                    endDate != null
                        ? 'End: ${endDate!.toLocal().toString().split(' ')[0]}'
                        : 'Select End Date',
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: getSunnyScore, // Trigger the sunny score calculation
            child: const Text('Get Sunny Score'),
          ),
          const SizedBox(height: 20),
          Text(
            sunnyScore.isEmpty ? 'Score will appear here' : 'Sunny Score: $sunnyScore',
            style: TextStyle(color: Colors.white, fontSize: 20),
          ),
          const SizedBox(height: 50),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.white, width: 2), // White border around checkbox
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Checkbox(
                  value: showAdvanced,
                  onChanged: (bool? value) {
                    setState(() {
                      showAdvanced = value ?? false;
                    });
                  },
                ),
              ),
              const Text("  Advanced Details", style: TextStyle(color: Colors.white, fontSize: 16)),
            ],
          ),
          if (showAdvanced)
            Container(
              padding: const EdgeInsets.all(10),
              margin: const EdgeInsets.only(top: 10),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Mean Clear Skies: $clearSkies%", style: TextStyle(color: Colors.white)),
                  Text("Mean Wind Speed: $windSpeed km/h", style: TextStyle(color: Colors.white)),
                  Text("Mean Rain: $rainScore mm", style: TextStyle(color: Colors.white)),
                  Text("Mean Snow: $snowScore mm", style: TextStyle(color: Colors.white)),
                ],
              ),
            ),  
        ],
      ),
    );
  }
}
