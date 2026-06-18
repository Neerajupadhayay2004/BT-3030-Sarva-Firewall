
import logging
import threading
from datetime import datetime
from pathlib import Path
from scapy.all import sniff, IP, TCP, UDP, ICMP, Raw

logger = logging.getLogger(__name__)

class ScapyPacketInspector:
    def __init__(self):
        self.is_sniffing = False
        self.sniff_thread = None
        self.captured_packets = []
        self.packet_callbacks = []
        self.lock = threading.Lock()
        
        # Store analyzed packets
        self.analyzed_packets = []
        logger.info("Scapy Packet Inspector initialized")
        
    def packet_handler(self, packet):
        with self.lock:
            try:
                packet_data = {}
                
                if IP in packet:
                    packet_data["source_ip"] = packet[IP].src
                    packet_data["dest_ip"] = packet[IP].dst
                    packet_data["protocol"] = "IP"
                    packet_data["ttl"] = packet[IP].ttl
                    packet_data["packet_size"] = len(packet)
                    
                    if TCP in packet:
                        packet_data["protocol"] = "TCP"
                        packet_data["source_port"] = packet[TCP].sport
                        packet_data["dest_port"] = packet[TCP].dport
                        packet_data["flags"] = str(packet[TCP].flags)
                        
                    elif UDP in packet:
                        packet_data["protocol"] = "UDP"
                        packet_data["source_port"] = packet[UDP].sport
                        packet_data["dest_port"] = packet[UDP].dport
                        
                    elif ICMP in packet:
                        packet_data["protocol"] = "ICMP"
                        packet_data["type"] = packet[ICMP].type
                        
                    if Raw in packet:
                        payload = str(packet[Raw].load)
                        packet_data["payload"] = payload[:200]
                        
                    packet_data["timestamp"] = datetime.utcnow().isoformat()
                    self.captured_packets.append(packet_data)
                    
                    # Notify callbacks
                    for callback in self.packet_callbacks:
                        try:
                            callback(packet_data)
                        except Exception as e:
                            logger.error(f"Error in packet callback: {e}")
                            
            except Exception as e:
                logger.error(f"Error processing packet: {e}")
                
    def start_sniffing(self, interface=None, filter_str=None):
        if self.is_sniffing:
            logger.warning("Already sniffing packets")
            return
            
        self.is_sniffing = True
        
        def sniff_loop():
            logger.info(f"Starting packet sniffing {'on interface ' + interface if interface else 'on all interfaces'}")
            try:
                sniff(
                    prn=self.packet_handler,
                    iface=interface,
                    filter=filter_str,
                    store=0
                )
            except Exception as e:
                logger.error(f"Sniffing error: {e}")
                self.is_sniffing = False
                
        self.sniff_thread = threading.Thread(target=sniff_loop, daemon=True)
        self.sniff_thread.start()
        
    def stop_sniffing(self):
        self.is_sniffing = False
        if self.sniff_thread and self.sniff_thread.is_alive():
            self.sniff_thread.join(timeout=2)
        logger.info("Stopped packet sniffing")
        
    def get_captured_packets(self, limit=100):
        with self.lock:
            return self.captured_packets[-limit:]
            
    def add_callback(self, callback_func):
        self.packet_callbacks.append(callback_func)
        logger.info("Added packet callback")
        
    def generate_test_packet(self, src_ip="192.168.1.100", dst_ip="192.168.1.1", 
                             src_port=12345, dst_port=80, protocol="TCP"):
        """Generate and process a test packet for testing"""
        from scapy.all import Ether
        test_packet = None
        
        if protocol == "TCP":
            test_packet = Ether() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags="S")
        elif protocol == "UDP":
            test_packet = Ether() / IP(src=src_ip, dst=dst_ip) / UDP(sport=src_port, dport=dst_port)
        elif protocol == "ICMP":
            test_packet = Ether() / IP(src=src_ip, dst=dst_ip) / ICMP()
            
        if test_packet:
            self.packet_handler(test_packet)
            return True
        return False
        
# Global instance
scapy_inspector = ScapyPacketInspector()
