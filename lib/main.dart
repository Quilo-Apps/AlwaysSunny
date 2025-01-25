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
  List<String> filters = ['Filter 1', 'Filter 2', 'Filter 3'];
  List<bool> filterSelections = [false, false, false];
  DateTime? startDate;
  DateTime? endDate;
  String city = '';
  String province = '';
  String sunnyScore = ''; // To hold the sunny score value

  // Function to fetch the sunny score from the backend
  Future<void> getSunnyScore() async {
  // Ensure city, startDate, and endDate are not null or empty
    if (city.isEmpty || startDate == null || endDate == null) {
      return;
    }

    final url = Uri.parse('http://127.0.0.1:5000/get_sunny_score'); // Your backend URL
    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: json.encode({
        'city': city,
        'province': province,
        'start_date': startDate!.toString().split(' ')[0], // Convert to YYYY-MM-DD
        'end_date': endDate!.toString().split(' ')[0], // Convert to YYYY-MM-DD
      }),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      setState(() {
        sunnyScore = data['sunny_score'].toString(); // Extract sunny_score from the response
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
        ],
      ),
    );
  }
}
