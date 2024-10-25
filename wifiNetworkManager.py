import asyncio
import subprocess
from networkController import wifi_manager, redis_client

# Bu koda https://github.com/abdulhamitmercan/networkProtokol adresinden erişebilirsiniz
# Bu kod, Wi-Fi bağlantısını yönetmek için bir sınıf tanımlar.
# Sınıf, Wi-Fi durumunu kontrol eder, internet bağlantısını test eder ve gerekli durum güncellemelerini Redis veritabanına kaydeder.
# Asenkron programlama ile Wi-Fi yönetimini sağlar.


wifi_enabled = wifi_manager.isEnabled()

class WiFi:
    def __init__(self):
        self.is_wifi_up = False
        self.is_wifi_first_check = True 
    async def get_wifi_info(self):
        print("Wi-Fi Bilgileri:")
       
        result = subprocess.run(['nmcli', '-f', 'SSID,SIGNAL,CHAN', 'device', 'wifi'], capture_output=True, text=True)
        if result.returncode == 0:
            if result.stdout.strip():
                print(result.stdout.strip())
            else:
                print("Wi-Fi ağı bulunamadı.")
        else:
            print("Wi-Fi bilgileri alınamadı.")
            print(f"Hata mesajı: {result.stderr.strip()}")

    async def check_wifi_status(self):
      
            if self.is_wifi_up:
                
                print("Wi-Fi aktive")
                
            else:
                print("Wi-Fi passive")

                await redis_client.hset("netWork", "wifiInternetStatus", "Wifi İnternet bağlantısı yok.")


    async def check_internet_connection(self):
        if self.is_wifi_up:
            print("Wi-Fi internet bağlantısı kontrol ediliyor...")
            result = subprocess.run(['ping', '-c', '1', '-I', 'wlan0', '8.8.8.8'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Wi-Fi internet bağlantısı mevcut.")
                await redis_client.hset("netWork", "wifiInternetStatus", "Wifi İnternet bağlantısı var.")
                await self.get_wifi_info()
            else:
                print("Wi-Fi internet bağlantısı yok.")
                print(f"Hata mesajı: {result.stderr.strip()}")  
                await redis_client.hset("netWork", "wifiInternetStatus", "Wifi İnternet bağlantısı yok.")
        else:
            print("Wi-Fi durumu: DOWN, internet bağlantısı kontrol edilemez.")
            await redis_client.hset("netWork", "wifiInternetStatus", "Wifi İnternet bağlantısı yok.")
    async def toggle_wifi(self):
        global wifi_enabled
        if wifi_enabled:
            if not self.is_wifi_up:
                print("Wi-Fi etkinleştiriliyor...")
                result = subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'], capture_output=True)
                if result.returncode == 0:
                    self.is_wifi_up = True
                    print("Wi-Fi etkinleşti.")
                else:
                    print("Wi-Fi etkinleştirilemedi.")
                    print(f"Hata mesajı: {result.stderr.strip()}")
        else:
            
            if self.is_wifi_first_check:
                self.is_wifi_up = True
                self.is_wifi_first_check = False
                
            if self.is_wifi_up:
                print("Wi-Fi devre dışı bırakılıyor...")
                result = subprocess.run(['sudo', 'ifconfig', 'wlan0', 'down'], capture_output=True)
                if result.returncode == 0:
                    self.is_wifi_up = False
                    print("Wi-Fi devre dışı kaldı.")
                else:
                    print("Wi-Fi devre dışı bırakılamadı.")
                    print(f"Hata mesajı: {result.stderr.strip()}")

    async def manage_wifi(self):
        while True:
            await self.check_wifi_status()
            await self.check_internet_connection()
            await self.toggle_wifi()
            await asyncio.sleep(5)  


