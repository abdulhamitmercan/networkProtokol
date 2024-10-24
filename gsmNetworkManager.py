import asyncio
import subprocess
from networkController import gsm_manager,redis_client

gsm_enabled = gsm_manager.isEnabled()  
gsmService = 'qmi_reconnect.service'


class GsmModule:
    def __init__(self):
        self.is_gsm_up = False  # Modem durumunu takip etmek için
        self.is_gsm_first_check = True  # İlk kontrol için flag

    async def run_at_command(self, command):
        # AT komutunu çalıştır
        result = subprocess.run(['atcom', command], capture_output=True, text=True)
        return result.stdout.strip()

    async def get_modem_name(self):
        modem_response = await self.run_at_command('AT+GMR')
        lines = modem_response.split('\n')
        modem_name = "Bilinmiyor"
        for line in lines:
            if line.strip() == "OK":
                break
            if line.strip() and not line.startswith('AT+GMR'):
                modem_name = line.strip()
        return modem_name

    async def check_sim(self):
        sim_response = await self.run_at_command('AT+CPIN?')
        sim_status = "SIM kart var." if "READY" in sim_response else "SIM kart yok."
        return sim_status

    async def get_apn_info(self):
        apn_response = await self.run_at_command('AT+CGDCONT?')
        apn_info = apn_response.split('"')[3] if 'CGDCONT' in apn_response and len(apn_response.split('"')) > 3 else "Bilinmiyor"
        return apn_info

    async def get_credentials(self):
        username_response = await self.run_at_command('AT+QICSGP=1')
        username_info = username_response.split('"')[3] if 'QICSGP' in username_response and len(username_response.split('"')) > 3 else "Bilinmiyor"
        password_info = username_response.split('"')[5] if 'QICSGP' in username_response and len(username_response.split('"')) > 5 else "Bilinmiyor"
        return username_info, password_info

    async def check_internet_connection(self):
        response = subprocess.run(['ping', '-I', 'wwan0', '-c', '1', '8.8.8.8'], capture_output=True)
        internet_status = "GSM İnternet bağlantısı var." if response.returncode == 0 else "GSM İnternet bağlantısı yok."
        await redis_client.hset("netWork", "gsmInternetStatus", internet_status)
                            
        return internet_status

    async def get_signal_strength(self):
        signal_response = await self.run_at_command('AT+CSQ')
        signal_strength = signal_response.split(':')[1].split(',')[0].strip() if "CSQ" in signal_response else "Bilgi alınamadı."
        return signal_strength

    async def evaluate_signal_strength(self, signal_strength, internet_status):
        try:
            csq_value = int(signal_strength)
            if csq_value < 10:  # Düşük sinyal durumu
                if internet_status == "GSM İnternet bağlantısı yok.":
                    return "Düşük çekim gücü ve internet bağlantısı yok: İnternet bağlantısı mümkün değil."
                return "Düşük çekim gücü: İnternet bağlantısı yavaşlayabilir."
            elif csq_value < 15:
                if internet_status == "GSM İnternet bağlantısı yok.":
                    return "Sinyal gücü düşük ancak internet bağlantısı yok."
                return "Sinyal gücü düşük: İnternet bağlantısı yavaşlayabilir."
            else:
                return "Sinyal gücü yeterli."
        except ValueError:
            return "Geçersiz sinyal gücü değeri."

    async def stop_service(self, service_name):
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=True)
            print(f"{service_name} servisi durduruldu.")
        except subprocess.CalledProcessError as e:
            print(f"Servisi durdururken bir hata oluştu: {e}")

    async def start_service(self, service_name):
        try:
            subprocess.run(['sudo', 'systemctl', 'start', service_name], check=True)
            print(f"{service_name} servisi başlatıldı.")
        except subprocess.CalledProcessError as e:
            print(f"Servisi başlatırken bir hata oluştu: {e}")

    async def run_all_checks(self):
        while True:
            if gsm_enabled:
                if not self.is_gsm_up:
                    await self.start_service(gsmService)
                    subprocess.run(['sudo', 'ifconfig', 'wwan0', 'up'])
                    self.is_gsm_up = True  # Modem durumu güncelle

                # Modem kontrolü
                modem_status = await self.run_at_command('AT')
                if "OK" in modem_status:
                    print("Modem bağlıdır.")
                    modem_name = await self.get_modem_name()
                    print(f"Modem Adı: {modem_name}")
                    await asyncio.sleep(0.001)

                    sim_status = await self.check_sim()
                    print(sim_status)

                    if sim_status == "SIM kart var.":
                        await asyncio.sleep(0.001)
                        apn_info = await self.get_apn_info()
                        print(f"APN: {apn_info}")
                        await asyncio.sleep(0.001)

                        username, password = await self.get_credentials()
                        print(f"Kullanıcı Adı: {username}")
                        print(f"Şifre: {password}")
                        await asyncio.sleep(0.001)

                        internet_status = await self.check_internet_connection()
                        print(internet_status)
                        if internet_status == "GSM İnternet bağlantısı var.":

                            await asyncio.sleep(0.001)
                            signal_strength = await self.get_signal_strength()
                            print(f"GSM İnternet çekme gücü: {signal_strength}")
                            
                            # Sinyal gücünü değerlendirme
                        signal_evaluation = await self.evaluate_signal_strength(signal_strength, internet_status)
                        print(signal_evaluation)

                else:
                    print("Modem bağlı değil veya yanıt alınamadı.")
            else:
                if self.is_gsm_first_check:
                    self.is_gsm_up = True
                    self.is_gsm_first_check = False
                if self.is_gsm_up:
                    await self.stop_service(gsmService)
                    subprocess.run(['sudo', 'ifconfig', 'wwan0', 'down'])
                    self.is_gsm_up = False  # Modem durumu güncelle
                    print("GSM Modem kapatıldı.")
            await asyncio.sleep(1)

# Asenkron ana döngü

