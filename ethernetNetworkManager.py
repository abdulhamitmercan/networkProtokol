import asyncio
import subprocess
from networkController import ethernet_manager,redis_client
# Çalışan kontrollü kod
ethernet_enabled = ethernet_manager.isEnabled()  # Ethernet durumunu kontrol etmek için kullanılacak

class Ethernet:
    def __init__(self):
        self._is_eth_up = False  # Ethernet durumunu saklamak için özel değişken
        self.cable_status = None  # Kablo durumunu saklayacak değişken

    @property
    def is_eth_up(self):
        return self._is_eth_up

    async def get_ethernet_info(self):
        print("Ethernet Bilgileri:")
        result = subprocess.run(['ethtool', 'eth0'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "Speed:" in line or "Duplex:" in line or "Auto-negotiation:" in line or "Link detected:" in line:
                print(line.strip())
        print("") 

    async def check_cable_status(self):
        # Kablo durumunu kontrol et ve duruma göre güncelle
        try:
            result = subprocess.run(['cat', '/sys/class/net/eth0/carrier'], capture_output=True, text=True)
            output = result.stdout.strip()
            if output == '':
                raise ValueError("Boş çıktı alındı.")  # Eğer çıktı boşsa hata fırlat
            self.cable_status = int(output)
            temp = self.cable_status 
        except (ValueError, subprocess.CalledProcessError):
            print("eternet  down durumda  ve geçersiz çıktı alındı.")
            self.cable_status = 0  # Kablo yok gibi varsay
            temp = 69 # bayburtun plakası diye alınmıştır manası yoktur
            
        if temp == 0:
            print("Kablo takılı değil .")
        if temp == 1:
            print("Kablo bağlı.")

    async def toggle_ethernet(self):
        # Ethernet durumunu kontrol et ve gerektiğindeN aç/kapat
        if ethernet_enabled:
            if not self.is_eth_up:  # Ethernet kapalıysa aç
                print("Ethernet etkinleştiriliyor...")
                subprocess.run(['sudo', 'ifconfig', 'eth0', 'up'])
                self._is_eth_up = True  # Durumu güncelle
                print("Ethernet etkin.")
        else:
            if self.is_eth_up:  # Ethernet açıksa kapat
                print("Ethernet devre dışı bırakılıyor...")
                subprocess.run(['sudo', 'ifconfig', 'eth0', 'down'])
                self._is_eth_up = False  # Durumu güncelle
                print("Ethernet devre dışı.")

    async def check_ethernet_status(self):
        # Ethernet arayüzünün durumunu kontrol et
        result = subprocess.run(['ip', 'link', 'show', 'eth0'], capture_output=True, text=True)
        if result.returncode == 0:
            if 'state UP' in result.stdout:
                print("Ethernet  aktive")
                self._is_eth_up = True  # Durumu güncelle
                await self.check_cable_status()  # Kablo durumunu kontrol et
                return True  # Arayüz aktif
            elif 'state DOWN' in result.stdout:
                print("Ethernet    passive")
                self._is_eth_up = False  # Durumu güncelle
                await self.check_cable_status()  # Kablo durumunu kontrol et
                return False  # Arayüz pasif
        return None  # Bir hata durumu

    async def check_internet_connection(self):
        # İnternet bağlantısını kontrol et
        if self.is_eth_up:  # Sadece Ethernet aktifse kontrol et
            print("ethernetin İnternet bağlantısı kontrol ediliyor...")
            result = subprocess.run(['ping', '-c', '1', '-I', 'eth0', '8.8.8.8'], capture_output=True, text=True)
            if result.returncode == 0:
                print("ethernetin İnternet bağlantısı mevcut.")
                await redis_client.hset("netWork", "ethernetInternetStatus", "Ethernet İnternet bağlantısı var.")
                await self.get_ethernet_info()  # Ethernet bilgilerini al
                return True
            else:
                print("ethernetin İnternet bağlantısı yok.")
                await redis_client.hset("netWork", "ethernetInternetStatus", "Ethernet İnternet bağlantısı yok.")
                return False
        else:
            print("Ethernet durumu: DOWN, internet bağlantısı kontrol edilemez.")
            await redis_client.hset("netWork", "ethernetInternetStatus", "Ethernet İnternet bağlantısı yok.") 
            return False

    async def manage_ethernet(self):
        # Ethernet durumunu sürekli kontrol et ve gerektiğinde aç/kapat
        while True:
            await self.check_cable_status()  # Kablo durumunu kontrol et
            if self.cable_status == 1:  # Kablo bağlıysa devam et
                await self.check_ethernet_status()  # Ethernet durumunu kontrol et
                await self.toggle_ethernet()         # Ethernet'i aç veya kapat
                await self.check_internet_connection() # İnternet bağlantısını kontrol et
            else:
                await self.toggle_ethernet()
                await redis_client.hset("netWork", "ethernetInternetStatus", "Ethernet İnternet bağlantısı yok.")
            await asyncio.sleep(5)  # Durum kontrolü arasında 5 saniye bekle

