# Generateur Horaire GUI

## Description
Generateur Horaire GUI is a graphical user interface application designed to facilitate the configuration of various options for executing the `generateur_horaire_v2.py` script. This application allows users to easily set parameters such as input files, output files, API URLs, and other options through an intuitive interface.

## Project Structure
```
generateur_horaire_gui
├── src
│   ├── main.py          # Entry point for the application
│   ├── gui.py           # Implementation of the graphical user interface
│   └── utils.py         # Utility functions for the application
├── requirements.txt      # List of dependencies
└── README.md             # Documentation for the project
```

## Installation
To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd generateur_horaire_gui
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the application, execute the following command:
```
python src/main.py
```

Once the application is running, you will be presented with a GUI that allows you to configure the necessary options for the `generateur_horaire_v2.py` script.

## Features
- User-friendly interface for configuring script options.
- Input fields for specifying file paths and API URLs.
- Options to include or exclude specific parameters.
- Validation of user input to ensure correct configurations.

## Contributing
Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.