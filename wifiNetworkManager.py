import asyncio
import subprocess
from networkController import wifi_manager, redis_client

# Global değişken
wifi_enabled = wifi_manager.isEnabled()

class WiFi:
    def __init__(self):
        self.is_wifi_up = False

    async def get_wifi_info(self):
        print("Wi-Fi Bilgileri:")
        # 'BAND' yerine 'CHAN' veya 'MODE' kullanıyoruz
        result = subprocess.run(['nmcli', '-f', 'SSID,SIGNAL,CHAN', 'device', 'wifi'], capture_output=True, text=True)
        if result.returncode == 0:
            if result.stdout.strip():
                print(result.stdout.strip())
            else:
                print("Wi-Fi ağı bulunamadı.")
        else:
            print("Wi-Fi bilgileri alınamadı.")
            print(f"Hata mesajı: {result.stderr.strip()}")  # Hata mesajını yazdır

    async def check_wifi_status(self):
        result = subprocess.run(['ip', 'link', 'show', 'wlan0'], capture_output=True, text=True)
        if result.returncode == 0:
            if 'state UP' in result.stdout:
                print("Wi-Fi aktive")
                self.is_wifi_up = True
            elif 'state DOWN' in result.stdout:
                print("Wi-Fi passive")
                self.is_wifi_up = False
                await redis_client.hset("netWork", "wifiInternetStatus", "Wifi İnternet bağlantısı yok.")
        else:
            print("Wi-Fi durumu kontrol edilirken hata oluştu.")
            print(f"Hata mesajı: {result.stderr.strip()}")  # Hata mesajını yazdır

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
                print(f"Hata mesajı: {result.stderr.strip()}")  # Hata mesajını yazdır
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
            await asyncio.sleep(5)  # Tüm işlemleri tekrar etmeden önce 5 saniye bekle


