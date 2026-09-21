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
    Innovation,
    InnovationPersonaRelevance,
    ResearchSuggestion
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


        print("[+] Seeding 8 Personas (Modul Pengguna)...")
        personas_data = [
            {"name": "Petani", "slug": "petani", "tagline": "Pelaku utama dalam produksi pangan dan pengelolaan lahan.", "icon_url": "sprout"},
            {"name": "Nelayan", "slug": "nelayan", "tagline": "Penggerak utama dalam pemanfaatan sumber daya kelautan.", "icon_url": "fish"},
            {"name": "Siswa / Mahasiswa", "slug": "siswa-mahasiswa", "tagline": "Generasi muda sebagai agen perubahan dan inovasi masa depan.", "icon_url": "graduation-cap"},
            {"name": "Pelaku Industri", "slug": "pelaku-industri", "tagline": "Penggerak inovasi dan penerapan teknologi di sektor industri.", "icon_url": "factory"},
            {"name": "Pemerintah", "slug": "pemerintah", "tagline": "Pembuat kebijakan dan pengambil keputusan strategis.", "icon_url": "building-columns"},
            {"name": "Pelaku Usaha", "slug": "pelaku-usaha", "tagline": "Pengusaha dan UMKM sebagai motor ekonomi dan inovasi.", "icon_url": "store"},
            {"name": "Peneliti / Akademisi", "slug": "peneliti-akademisi", "tagline": "Pendorong riset fundamental, terapan, dan inovasi ilmiah.", "icon_url": "microscope"},
            {"name": "Masyarakat Umum", "slug": "masyarakat-umum", "tagline": "Penerima manfaat inovasi dan pengguna solusi teknologi harian.", "icon_url": "users"},
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

        print("[+] Seeding 9 Research Zones (Modul Tantangan BRIN)...")
        zones_data = [
            {"name": "Biodiversitas", "slug": "biodiversitas", "description": "Keanekaragaman hayati, konservasi, dan sumber daya hayati.", "icon_url": "leaf"},
            {"name": "Pangan", "slug": "pangan", "description": "Ketahanan pangan, produktivitas pertanian, dan distribusi.", "icon_url": "wheat"},
            {"name": "Kesehatan", "slug": "kesehatan", "description": "Diagnostik, pencegahan penyakit, dan kualitas hidup.", "icon_url": "heart-pulse"},
            {"name": "Industri", "slug": "industri", "description": "Manufaktur, material, otomasi, dan daya saing industri.", "icon_url": "cog"},
            {"name": "Energi", "slug": "energi", "description": "Energi bersih, efisiensi, penyimpanan, dan kemandirian.", "icon_url": "bolt"},
            {"name": "Digital", "slug": "digital", "description": "Kecerdasan artifisial, komputasi awan, big data, dan keamanan siber.", "icon_url": "cpu"},
            {"name": "Dirgantara", "slug": "dirgantara", "description": "Satelit, penginderaan jauh, aeronautika, dan eksplorasi antariksa.", "icon_url": "rocket"},
            {"name": "Nuklir", "slug": "nuklir", "description": "Teknologi nuklir untuk energi, kesehatan, industri, dan radiasi.", "icon_url": "atom"},
            {"name": "Transportasi", "slug": "transportasi", "description": "Mobilitas berkelanjutan, kendaraan listrik, dan infrastruktur transportasi.", "icon_url": "truck"},
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

        print("[+] Seeding Inovasi BRIN (PDF Catalog & Extensions)...")
        innovations_data = [
            {
                "zone_slug": "energi",
                "title": "Battery Monitoring Platform",
                "slug": "battery-monitoring-platform",
                "trl": 7,
                "short_description": "Platform IoT cerdas untuk memantau performa, suhu, dan degradasi sel baterai secara real-time.",
                "summary": "Solusi riset BRIN yang dikembangkan untuk mendukung penerapan teknologi pada konteks energi terdesentralisasi dan kendaraan listrik.",
                "impact": "Memantau performa dan kondisi sistem penyimpanan energi, memperpanjang usia baterai hingga 30%, dan mencegah insiden thermal runaway.",
                "persona_weights": {"petani": 75, "pelaku-industri": 95, "siswa-mahasiswa": 80, "pemerintah": 85, "pelaku-usaha": 90}
            },
            {
                "zone_slug": "energi",
                "title": "Microgrid Controller",
                "slug": "microgrid-controller",
                "trl": 7,
                "short_description": "Pengendali integrasi pembangkit surya, angin, dan genset untuk keandalan listrik daerah 3T.",
                "summary": "Sistem kontrol otomatis yang menyeimbangkan beban dan suplai listrik dari aneka pembangkit energi terbarukan lokal secara mandiri.",
                "impact": "Menjamin kestabilan pasokan listrik 24 jam di pedesaan, pulau terpencil, dan sentra produksi tanpa bergantung pada jaringan transmisi utama.",
                "persona_weights": {"petani": 85, "pelaku-industri": 90, "pemerintah": 95, "nelayan": 80}
            },
            {
                "zone_slug": "energi",
                "title": "Bioenergi dari Limbah Organik",
                "slug": "bioenergi-dari-limbah-organik",
                "trl": 6,
                "short_description": "Reaktor biogas & biofuel modular pemroses limbah pertanian dan perkebunan menjadi energi listrik dan gas masak.",
                "summary": "Teknologi konversi biomassa limbah sekam padi, kotoran ternak, dan cangkang sawit menjadi bahan bakar alternatif bernilai ekonomi tinggi.",
                "impact": "Mengurangi biaya energi operasional petani/UMKM hingga 40% sekaligus menyelesaikan masalah pencemaran limbah lingkungan.",
                "persona_weights": {"petani": 100, "pelaku-usaha": 85, "masyarakat-umum": 80, "pelaku-industri": 75}
            },
            {
                "zone_slug": "pangan",
                "title": "Smart Irrigation & Soil Sensor System",
                "slug": "smart-irrigation-soil-sensor",
                "trl": 7,
                "short_description": "Sistem sensor kelembapan tanah nirkabel terhubung pompa otomatis untuk efisiensi air dan nutrisi tanaman.",
                "summary": "Perangkat IoT pertanian yang memantau pH tanah, kelembapan, dan kandungan NPK secara presisi melalui dasbor smartphone.",
                "impact": "Menghemat konsumsi air irigasi 45% dan meningkatkan hasil panen padi serta hortikultura hingga 25%.",
                "persona_weights": {"petani": 100, "siswa-mahasiswa": 85, "pelaku-usaha": 80, "pemerintah": 80}
            },
            {
                "zone_slug": "digital",
                "title": "AI Satellite Maritime Surveillance",
                "slug": "ai-satellite-maritime-surveillance",
                "trl": 8,
                "short_description": "Kecerdasan buatan pemroses citra satelit dan AIS untuk mendeteksi illegal fishing dan zona tangkapan ikan potensial.",
                "summary": "Algoritma deep learning yang mampu memetakan lokasi berkumpulnya ikan secara real-time dan memberikan peta navigasi ke nelayan.",
                "impact": "Mempersingkat waktu pencarian ikan di laut hingga 50%, menghemat BBM nelayan, dan memperkuat kedaulatan maritim.",
                "persona_weights": {"nelayan": 100, "pemerintah": 95, "peneliti-akademisi": 85, "pelaku-industri": 80}
            }
        ]

        for inno_data in innovations_data:
            zone = zone_map.get(inno_data["zone_slug"])
            weights = inno_data.pop("persona_weights", {})
            z_slug = inno_data.pop("zone_slug")

            top_persona_slug = max(weights, key=weights.get)
            top_persona = persona_map.get(top_persona_slug)

            inno_obj = db.query(Innovation).filter(Innovation.slug == inno_data["slug"]).first()
            if not inno_obj:
                inno_obj = Innovation(
                    zone_id=zone.id,
                    persona_id=top_persona.id if top_persona else None,
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
