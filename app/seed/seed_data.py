import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models import (
    User,
    Persona,
    Zone,
    ResearchCenter,
    Innovation,
    InnovationPersonaRelevance,
    ResearchSuggestion,
    AppSetting
)


def seed_database():
    print("[+] Initializing Database Tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[+] Tables created successfully!")

    db = SessionLocal()
    try:
        print("[+] Seeding Admin User...")
        admin = db.query(User).filter((User.username == "admin") | (User.email == "admin@brin.go.id")).first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@brin.go.id",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator BRIN",
                role="superadmin",
                is_active=1
            )
            db.add(admin)
            db.commit()
            print("[+] Admin created: username='admin' (Password: admin123)")
        else:
            print("[i] Admin already exists.")

        print("[+] Seeding App Settings...")
        setting = db.query(AppSetting).filter(AppSetting.key == "frontend_display_limit").first()
        if not setting:
            setting = AppSetting(key="frontend_display_limit", value="50", description="Batas kuota inovasi di layar sentuh")
            db.add(setting)
            db.commit()
            print("[+] Default settings created.")

        print("[+] Seeding 8 Personas (Modul Pengguna)...")
        personas_data = [
            {"name": "Petani", "slug": "petani", "tagline": "Pelaku utama dalam produksi pangan dan pengelolaan lahan.", "icon_name": "sprout", "order_index": 1},
            {"name": "Nelayan", "slug": "nelayan", "tagline": "Penggerak utama dalam pemanfaatan sumber daya kelautan.", "icon_name": "fish", "order_index": 2},
            {"name": "Siswa / Mahasiswa", "slug": "siswa-mahasiswa", "tagline": "Generasi muda sebagai agen perubahan dan inovasi masa depan.", "icon_name": "graduation-cap", "order_index": 3},
            {"name": "Pelaku Industri", "slug": "pelaku-industri", "tagline": "Penggerak inovasi dan penerapan teknologi di sektor industri.", "icon_name": "factory", "order_index": 4},
            {"name": "Pemerintah", "slug": "pemerintah", "tagline": "Pembuat kebijakan dan pengambil keputusan strategis.", "icon_name": "building-columns", "order_index": 5},
            {"name": "Pelaku Usaha", "slug": "pelaku-usaha", "tagline": "Pengusaha dan UMKM sebagai motor ekonomi dan inovasi.", "icon_name": "store", "order_index": 6},
            {"name": "Peneliti / Akademisi", "slug": "peneliti-akademisi", "tagline": "Pendorong riset fundamental, terapan, dan inovasi ilmiah.", "icon_name": "microscope", "order_index": 7},
            {"name": "Masyarakat Umum", "slug": "masyarakat-umum", "tagline": "Penerima manfaat inovasi dan pengguna solusi teknologi harian.", "icon_name": "users", "order_index": 8},
        ]

        persona_map = {}
        for p in personas_data:
            obj = db.query(Persona).filter(Persona.slug == p["slug"]).first()
            if not obj:
                obj = Persona(**p)
                db.add(obj)
                db.commit()
                db.refresh(obj)
            persona_map[obj.slug] = obj
        print("[+] 8 Personas ready.")

        print("[+] Seeding 9 Research Zones (Token Tantangan BRIN)...")
        zones_data = [
            {"zone_number": 1, "name": "Biodiversitas", "slug": "biodiversitas", "description": "Keanekaragaman hayati, konservasi, dan sumber daya hayati.", "color_theme": "#10b981", "icon_name": "leaf", "order_index": 1},
            {"zone_number": 2, "name": "Pangan", "slug": "pangan", "description": "Ketahanan pangan, produktivitas pertanian, dan distribusi.", "color_theme": "#f59e0b", "icon_name": "wheat", "order_index": 2},
            {"zone_number": 3, "name": "Kesehatan", "slug": "kesehatan", "description": "Diagnostik, pencegahan penyakit, dan kualitas hidup.", "color_theme": "#ef4444", "icon_name": "heart-pulse", "order_index": 3},
            {"zone_number": 4, "name": "Industri", "slug": "industri", "description": "Manufaktur, material, otomasi, dan daya saing industri.", "color_theme": "#8b5cf6", "icon_name": "cog", "order_index": 4},
            {"zone_number": 5, "name": "Energi", "slug": "energi", "description": "Energi bersih, efisiensi, penyimpanan, dan kemandirian.", "color_theme": "#3b82f6", "icon_name": "bolt", "order_index": 5},
            {"zone_number": 6, "name": "Digital", "slug": "digital", "description": "Kecerdasan artifisial, komputasi awan, big data, dan keamanan siber.", "color_theme": "#06b6d4", "icon_name": "cpu", "order_index": 6},
            {"zone_number": 7, "name": "Dirgantara", "slug": "dirgantara", "description": "Satelit, penginderaan jauh, aeronautika, dan eksplorasi antariksa.", "color_theme": "#6366f1", "icon_name": "rocket", "order_index": 7},
            {"zone_number": 8, "name": "Nuklir", "slug": "nuklir", "description": "Teknologi nuklir untuk energi, kesehatan, industri, dan radiasi.", "color_theme": "#ec4899", "icon_name": "atom", "order_index": 8},
            {"zone_number": 9, "name": "Transportasi", "slug": "transportasi", "description": "Mobilitas berkelanjutan, kendaraan listrik, dan infrastruktur transportasi.", "color_theme": "#14b8a6", "icon_name": "truck", "order_index": 9},
        ]

        zone_map = {}
        for z in zones_data:
            obj = db.query(Zone).filter(Zone.slug == z["slug"]).first()
            if not obj:
                obj = Zone(**z)
                db.add(obj)
                db.commit()
                db.refresh(obj)
            zone_map[obj.slug] = obj
        print("[+] 9 Research Zones ready.")

        print("[+] Seeding Research Centers (Pusat Riset BRIN)...")
        centers_data = [
            {"name": "Pusat Riset Konversi dan Konservasi Energi", "or_name": "Organisasi Riset Energi dan Manufaktur", "code": "PRKKE", "description": "Riset konversi energi baru terbarukan dan penyimpanan energi."},
            {"name": "Pusat Riset Sistem Energi", "or_name": "Organisasi Riset Energi dan Manufaktur", "code": "PRSE", "description": "Pengembangan smart grid dan microgrid controller."},
            {"name": "Pusat Riset Hortikultura dan Tanaman Pangan", "or_name": "Organisasi Riset Pertanian dan Pangan", "code": "PRHTP", "description": "Pemuliaan varietas unggul tahan iklim."},
            {"name": "Pusat Riset Kelautan dan Sumber Daya Hayati Laut", "or_name": "Organisasi Riset Kebumian dan Maritim", "code": "PRKSDHL", "description": "Biofarmaka laut dan navigasi tangkap."},
            {"name": "Pusat Riset Kecerdasan Artifisial dan Keamanan Siber", "or_name": "Organisasi Riset Informatika", "code": "PRAISS", "description": "AI terapan dan citra satelit maritim."},
            {"name": "Pusat Riset Teknologi Satelit dan Dirgantara", "or_name": "Organisasi Riset Penerbangan dan Antariksa", "code": "PRTSD", "description": "Pengembangan konstelasi satelit mikro."},
            {"name": "Pusat Riset Teknologi Daur Bahan Bakar Nuklir dan Limbah Radioaktif", "or_name": "Organisasi Riset Tenaga Nuklir", "code": "PRTDBN", "description": "Aplikasi teknologi nuklir untuk pangan dan medis."},
            {"name": "Pusat Riset Teknologi Transportasi", "or_name": "Organisasi Riset Energi dan Manufaktur", "code": "PRTT", "description": "Rancang bangun powertrain kendaraan listrik."},
        ]

        center_map = {}
        for c in centers_data:
            obj = db.query(ResearchCenter).filter(ResearchCenter.name == c["name"]).first()
            if not obj:
                obj = ResearchCenter(**c)
                db.add(obj)
                db.commit()
                db.refresh(obj)
            center_map[obj.code] = obj
        print("[+] Research Centers ready.")

        print("[+] Seeding Inovasi BRIN (PDF Catalog & Extensions)...")
        innovations_data = [
            {
                "zone_slug": "energi",
                "center_code": "PRKKE",
                "title": "Battery Monitoring Platform",
                "slug": "battery-monitoring-platform",
                "category_tag": "Penyimpanan Energi",
                "trl": 7,
                "short_description": "Platform IoT cerdas untuk memantau performa, suhu, dan degradasi sel baterai secara real-time.",
                "summary": "Solusi riset BRIN yang dikembangkan untuk mendukung penerapan teknologi pada konteks energi terdesentralisasi dan kendaraan listrik.",
                "impact": "Memantau performa dan kondisi sistem penyimpanan energi, memperpanjang usia baterai hingga 30%, dan mencegah insiden thermal runaway.",
                "order_priority": 95,
                "persona_weights": {"petani": 75, "pelaku-industri": 95, "siswa-mahasiswa": 80, "pemerintah": 85, "pelaku-usaha": 90}
            },
            {
                "zone_slug": "energi",
                "center_code": "PRSE",
                "title": "Microgrid Controller",
                "slug": "microgrid-controller",
                "category_tag": "Sistem Energi",
                "trl": 7,
                "short_description": "Pengendali integrasi pembangkit surya, angin, dan genset untuk keandalan listrik daerah 3T.",
                "summary": "Sistem kontrol otomatis yang menyeimbangkan beban dan suplai listrik dari aneka pembangkit energi terbarukan lokal secara mandiri.",
                "impact": "Menjamin kestabilan pasokan listrik 24 jam di pedesaan, pulau terpencil, dan sentra produksi tanpa bergantung pada jaringan transmisi utama.",
                "order_priority": 90,
                "persona_weights": {"petani": 85, "pelaku-industri": 90, "pemerintah": 95, "nelayan": 80}
            },
            {
                "zone_slug": "energi",
                "center_code": "PRKKE",
                "title": "Bioenergi dari Limbah Organik",
                "slug": "bioenergi-dari-limbah-organik",
                "category_tag": "Bioenergi",
                "trl": 6,
                "short_description": "Reaktor biogas & biofuel modular pemroses limbah pertanian dan perkebunan menjadi energi listrik dan gas masak.",
                "summary": "Teknologi konversi biomassa limbah sekam padi, kotoran ternak, dan cangkang sawit menjadi bahan bakar alternatif bernilai ekonomi tinggi.",
                "impact": "Mengurangi biaya energi operasional petani/UMKM hingga 40% sekaligus menyelesaikan masalah pencemaran limbah lingkungan.",
                "order_priority": 98,
                "persona_weights": {"petani": 100, "pelaku-usaha": 85, "masyarakat-umum": 80, "pelaku-industri": 75}
            },
            {
                "zone_slug": "pangan",
                "center_code": "PRHTP",
                "title": "Smart Irrigation & Soil Sensor System",
                "slug": "smart-irrigation-soil-sensor",
                "category_tag": "Pertanian Presisi",
                "trl": 7,
                "short_description": "Sistem sensor kelembapan tanah nirkabel terhubung pompa otomatis untuk efisiensi air dan nutrisi tanaman.",
                "summary": "Perangkat IoT pertanian yang memantau pH tanah, kelembapan, dan kandungan NPK secara presisi melalui dasbor smartphone.",
                "impact": "Menghemat konsumsi air irigasi 45% dan meningkatkan hasil panen padi serta hortikultura hingga 25%.",
                "order_priority": 95,
                "persona_weights": {"petani": 100, "siswa-mahasiswa": 85, "pelaku-usaha": 80, "pemerintah": 80}
            },
            {
                "zone_slug": "digital",
                "center_code": "PRAISS",
                "title": "AI Satellite Maritime Surveillance",
                "slug": "ai-satellite-maritime-surveillance",
                "category_tag": "Kecerdasan Artifisial",
                "trl": 8,
                "short_description": "Kecerdasan buatan pemroses citra satelit dan AIS untuk mendeteksi illegal fishing dan zona tangkapan ikan potensial.",
                "summary": "Algoritma deep learning yang mampu memetakan lokasi berkumpulnya ikan secara real-time dan memberikan peta navigasi ke nelayan.",
                "impact": "Mempersingkat waktu pencarian ikan di laut hingga 50%, menghemat BBM nelayan, dan memperkuat kedaulatan maritim.",
                "order_priority": 95,
                "persona_weights": {"nelayan": 100, "pemerintah": 95, "peneliti-akademisi": 85, "pelaku-industri": 80}
            }
        ]

        for inno_data in innovations_data:
            zone = zone_map.get(inno_data["zone_slug"])
            center = center_map.get(inno_data["center_code"])
            weights = inno_data.pop("persona_weights", {})
            z_slug = inno_data.pop("zone_slug")
            c_code = inno_data.pop("center_code")

            inno_obj = db.query(Innovation).filter(Innovation.slug == inno_data["slug"]).first()
            if not inno_obj:
                inno_obj = Innovation(
                    zone_id=zone.id,
                    research_center_id=center.id if center else None,
                    **inno_data
                )
                db.add(inno_obj)
                db.commit()
                db.refresh(inno_obj)

            for p_slug, score in weights.items():
                p_obj = persona_map.get(p_slug)
                if p_obj:
                    rel_obj = db.query(InnovationPersonaRelevance).filter(
                        InnovationPersonaRelevance.innovation_id == inno_obj.id,
                        InnovationPersonaRelevance.persona_id == p_obj.id
                    ).first()
                    if not rel_obj:
                        rel_obj = InnovationPersonaRelevance(
                            innovation_id=inno_obj.id,
                            persona_id=p_obj.id,
                            relevance_score=score
                        )
                        db.add(rel_obj)
            db.commit()
        print("[+] Innovations & Persona relevance mapping ready.")

    finally:
        db.close()
    print("\n[+] ALL SEEDING COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    seed_database()
