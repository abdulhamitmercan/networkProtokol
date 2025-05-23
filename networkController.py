import asyncio
from debug_logger import DebugLogger
from gsmNetworkManager import GsmModule
from ethernetNetworkManager import Ethernet
from wifiNetworkManager import WiFi
from networkUtils import NetworkManager



# Bu koda https://github.com/abdulhamitmercan/networkProtokol adresinden erişebilirsiniz
# Kod, asenkron programlama ile çoklu bağlantıları yönetmeyi ve güncellemeyi sağlar.



logger = DebugLogger(level=DebugLogger.LEVEL_INFO, format_type=DebugLogger.FORMAT_FULL, log_file_path='network.log')
async def main():

    
    network_manager = NetworkManager(logger)
    gsm_module = GsmModule(logger)
    ethernet_control = Ethernet(logger)
    wifi_manager = WiFi(logger)

    await asyncio.gather(
        network_manager.internet_check_and_update(),
        gsm_module.manage_gsm(),
        ethernet_control.manage_ethernet(),
        wifi_manager.manage_wifi()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Event loop'u başlat ve tamamla
    except RuntimeError as e:
        print(f"Hata: {e}")