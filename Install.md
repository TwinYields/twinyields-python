
# Install TwinYields dependencies and libraries on Ubuntu 20.04

## Install Dotnet SDK 6

https://docs.microsoft.com/en-us/dotnet/core/install/linux-ubuntu#2004

## Install MongoDB and add authentication

https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/
https://www.mongodb.com/docs/manual/tutorial/configure-scram-client-authentication/


## Install packages

```
sudo apt-get install libsqlite3-dev libgdal-dev python3-pip
```

## Install Miniconda

wget -c https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh

## Install Python library

```
cd ~/git
python3 -m pip install --upgrade pip
git clone https://github.com/TwinYields/twinyields-python.git
cd twinyields-python
python3 -m pip install -r requirements.txt --no-deps .
```

## Install C# library

```
cd ~/git
git clone --recurse-submodules git@github.com:TwinYields/TwinYields.git
dotnet publish -c Release ~/git/TwinYields/TwinConsole/TwinConsole.csproj -o ~/DigitalTwin/TwinConsole
```

## Edit configuration

Copy the template and edit to add login information

```bash
mkdir ~/.twinyields
cp ~/git/twinyields-python/config/config.toml ~/.twinyields
```

## Edit crontab  to run on schedule

`crontab -e`

```
PATH=/bin:/usr/bin:/home/digitaltwin/.local/bin

0,15,30,45 * * * * twinyields -s >> twin.log
0 0  * * * twinyields -e >> twin.log
0 1 * * * twinyields -r >> twin.log
```