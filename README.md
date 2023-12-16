
# Strip Alerts

## Description
This project allows controlling NeoPixels based on API events.

## Installation
To run this project, you will need Python installed on your system.

Clone the repository and install the required dependencies:
```bash
cd
git clone https://github.com/MountainGod2/stripalerts/
cd ~/stripalerts
pip install -r requirements.txt
```

## Configuration
Configure the NeoPixel settings in `config.py`.
This includes parameters like the number of pixels, pin configuration, animation speed, and brightness.
```bash
cd ~/stripalerts
nano src/config.py
```


## Credentials
To set up your `config.ini` file for credentials, use the following command.
Replace `example_username` and `example_password` with your actual data, and the script will encode it in base64:

```bash
cd ~/stripalerts
echo -e "[Credentials]\n\
user_name=$(echo -n 'example_username' | base64)\n\
api_token=$(echo -n 'example_password' | base64)" > config.ini
```

***Note:*** While the username and api_token are being encoded in base64, this does not provide additional
security and is simply to keep from storing the keys in plaintext. *However, this is not encryption and should not
be treated as such.*

(Example `config.ini` using the command above)
```ini
[Credentials]
user_name=ZXhhbXBsZV91c2VybmFtZQ==
api_token=ZXhhbXBsZV9wYXNzd29yZA==

```
***DO NOT SHARE THIS FILE***

## Usage
Run the `main.py` script to start the application:

```bash
cd stripalerts/
python src/main.py
```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License - see the [LICENSE](https://github.com/MountainGod2/stripalerts/blob/main/LICENSE) file for details.

