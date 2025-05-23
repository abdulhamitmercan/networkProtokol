from debug_logger import DebugLogger
import redis.asyncio as redis
import asyncio

# Bu kod Abdulhamit Mercan tarafından Ekim 2024'te yazılmıştır.
# Bu koda https://github.com/abdulhamitmercan/networkProtokol adresinden erişebilirsiniz
# Bu kod, Wi-Fi, Ethernet ve GSM bağlantılarını yönetmek için çeşitli sınıflar içerir.
# Bu yöneticiler, belirli bir durumda hangi bağlantının etkinleştirileceğini veya devre dışı bırakılacağını kontrol eder.
# Ayrıca, Redis veritabanından alınan "caseVal" değerine göre bağlantı durumunu sürekli günceller.
# sistem loglanmıştır


class WifiManager:
    def __init__(self):
        self._enabled = True 

    def setEnabled(self, value):
        self._enabled = value

    def isEnabled(self):
        return self._enabled

    async def enable(self):
        # print("Wi-Fi etkinleştirildi.")
        self.setEnabled(True)

    async def disable(self):
        # print("Wi-Fi devre dışı bırakıldı.")
        self.setEnabled(False)


class EthernetManager:
    def __init__(self):
        self._enabled = True

    def setEnabled(self, value):
        self._enabled = value

    def isEnabled(self):
        return self._enabled

    async def enable(self):
        # print("Ethernet etkinleştirildi.")
        self.setEnabled(True)

    async def disable(self):
        # print("Ethernet devre dışı bırakıldı.")
        self.setEnabled(False)


class GsmManager:
    def __init__(self):
        self._enabled = True

    def setEnabled(self, value):
        self._enabled = value

    def isEnabled(self):
        return self._enabled

    async def enable(self):
        # print("GSM etkinleştirildi.")
        self.setEnabled(True)

    async def disable(self):
        # print("GSM devre dışı bırakıldı.")
        self.setEnabled(False)


wifi_manager = WifiManager()
ethernet_manager = EthernetManager()
gsm_manager = GsmManager()
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class NetworkManager:
    def __init__(self,logger=None):
        self._case_number = 8  
        self.logger = logger
        
    def set_case_number(self, case_number):
        self._case_number = case_number

    def get_case_number(self):
        return self._case_number

    async def handle_case(self, case_number):
        if case_number == '1':
            await wifi_manager.enable()
            await ethernet_manager.disable()
            await gsm_manager.disable()
        elif case_number == '2':
            await ethernet_manager.enable()
            await wifi_manager.disable()
            await gsm_manager.disable()
        elif case_number == '3':
            await gsm_manager.enable()
            await wifi_manager.disable()
            await ethernet_manager.disable()
        elif case_number == '4':
            await wifi_manager.enable()
            await ethernet_manager.enable()
            await gsm_manager.disable()
        elif case_number == '5':
            await wifi_manager.enable()
            await gsm_manager.enable()
            await ethernet_manager.disable()
        elif case_number == '6':
            await ethernet_manager.enable()
            await gsm_manager.enable()
            await wifi_manager.disable()
        elif case_number == '7':
            await wifi_manager.enable()
            await ethernet_manager.enable()
            await gsm_manager.enable()
        elif case_number == '8':
            await wifi_manager.disable()
            await ethernet_manager.disable()
            await gsm_manager.disable()
        else:
            self.logger.error("", filename="networkController.py", category="network stuation", status="geçersiz case numarası")
            # print("Geçersiz case numarası.")

    async def internet_check_and_update(self):
        while True:
            case_value = await redis_client.hget("netWork", "caseVal")
            if case_value is None:
                self.logger.error("", filename="networkController.py", category="network stuation", status="Redis'ten caseVal değeri alınamadı, varsayılan bir değer(7) atanıyor")
               # print("Redis'ten caseVal değeri alınamadı, varsayılan bir değer atanıyor.")
                case_value = '7'
                await asyncio.sleep(2)
            else:
                case_value = int(case_value)
            
            self.set_case_number(case_value)
