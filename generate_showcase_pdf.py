import os
from fpdf import FPDF

class JodoPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(99, 102, 241)  # Jodo Secondary color
        self.cell(0, 20, 'Jodo Sandbox Evolution V1 - Showcase', ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf():
    pdf = JodoPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGE 1: Vision & Rationale ---
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 15, 'Project Vision', ln=True)
    pdf.set_font('helvetica', '', 11)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 6, 'The Jodo Sandbox Evolution is a production-grade, self-service developer portal designed to accelerate integration scaling. By providing a high-fidelity, standalone environment, we enable developers to build, test, and iterate on Jodo payments with zero friction and 100% confidence.')
    pdf.ln(10)

    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 15, 'Scaling Integration Rationale', ln=True)
    
    rationales = [
        ("Secure Onboarding", "Dedicated login and signup pages for developer-specific access control."),
        ("Zero-Friction Credentialing", "Providing pre-computed Authorization Headers removes manual encoding friction."),
        ("Schema Fidelity", "Official Jodo nested details schema for production-ready testing."),
        ("Realistic Simulation", "Two-stage checkout mirroring real-world latency and UI transitions."),
        ("Real-time Observability", "Instant reflection of transactions and webhook delivery logs.")
    ]
    
    for title, desc in rationales:
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 8, f'- {title}', ln=True)
        pdf.set_font('helvetica', '', 11)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 6, desc)
        pdf.ln(2)

    # --- PAGE 2: Developer Onboarding ---
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 15, 'Developer Onboarding: Secure Access', ln=True)
    
    pdf.set_font('helvetica', '', 11)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 6, 'Developers begin their journey by creating a dedicated sandbox account. This ensures that all API keys, webhook configurations, and transaction logs are isolated and secure.')
    pdf.ln(5)

    auth_screens = [
        ("Login Portal", "/Users/manojaaa/.gemini/antigravity/brain/652e00bd-d010-48f9-a820-23b5c6a74258/jodo_login_page_1775102370547.png"),
        ("Signup / Instance Initialization", "/Users/manojaaa/.gemini/antigravity/brain/652e00bd-d010-48f9-a820-23b5c6a74258/jodo_signup_page_1775102380743.png")
    ]

    for title, img_path in auth_screens:
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, title, ln=True)
        if os.path.exists(img_path):
            pdf.image(img_path, w=150)
            pdf.ln(10)
        else:
            pdf.cell(0, 10, f'[Image Missing: {os.path.basename(img_path)}]', ln=True)

    # --- PAGE 3: Credentials & Prototyping ---
    pdf.add_page()
    
    journey_sections = [
        ("Step 1: Accessing Secure Credentials", 
         "The dashboard provides a clear Base URL and a revealed Authorization Header for immediate integration.",
         "/Users/manojaaa/.gemini/antigravity/brain/652e00bd-d010-48f9-a820-23b5c6a74258/api_keys_revealed_1775101268822.png"),
        ("Step 2: Prototyping in the Playground", 
         "The playground uses the official Jodo schema. The 'Copy Curl' utility injects headers automatically.",
         "/Users/manojaaa/.gemini/antigravity/brain/652e00bd-d010-48f9-a820-23b5c6a74258/api_playground_response_success_1775101017930.png")
    ]

    for title, desc, img_path in journey_sections:
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font('helvetica', '', 11)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 6, desc)
        pdf.ln(5)
        if os.path.exists(img_path):
            pdf.image(img_path, w=180)
            pdf.ln(10)

    # --- PAGE 4: Simulation & Real-time Metrics ---
    pdf.add_page()
    
    simulation_sections = [
        ("Step 3: Realistic Checkout Flow", 
         "Simulates the Jodo client experience with brand-consistent Rupee formatting and correct terminology.",
         "/Users/manojaaa/.gemini/antigravity/brain/652e00bd-d010-48f9-a820-23b5c6a74258/jodo_sandbox_collection_page_1775101041934.png"),
        ("Step 4: Success Verification", 
         "A clean outcome page mirroring production success receipts.",
         "/Users/manojaaa/.gemini/antigravity/brain/652e00bd-d010-48f9-a820-23b5c6a74258/payment_successful_result_page_1775101137163.png")
    ]

    for title, desc, img_path in simulation_sections:
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font('helvetica', '', 11)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 6, desc)
        pdf.ln(5)
        if os.path.exists(img_path):
            pdf.image(img_path, w=180)
            pdf.ln(10)

    # --- PAGE 5: Observability & Logs (UPDATED) ---
    pdf.add_page()
    
    observability_sections = [
        ("Transaction History & Lifecycle", 
         "Every transaction is logged with real-time status updates (CREATED, PAID).",
         "/Users/manojaaa/.gemini/antigravity/brain/652e00bd-d010-48f9-a820-23b5c6a74258/media__1775102116675.png"),
        ("Webhook Delivery Observability", 
         "Granular logs detailing delivery status and timestamps for backend verification.",
         "/Users/manojaaa/.gemini/antigravity/brain/652e00bd-d010-48f9-a820-23b5c6a74258/media__1775102109320.png")
    ]

    for title, desc, img_path in observability_sections:
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font('helvetica', '', 11)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 6, desc)
        pdf.ln(5)
        if os.path.exists(img_path):
            pdf.image(img_path, w=180)
            pdf.ln(10)

    # Final Summary
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(16, 185, 129)  # Success Green
    pdf.cell(0, 15, 'V1 Scaling Complete', ln=True)
    pdf.set_font('helvetica', '', 11)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 6, 'This standalone sandbox is fully operational and provides a high-performance, self-service path for developer onboarding and integration testing.')

    pdf.output('jodo_v1_scaling_showcase_v2.pdf')
    print("PDF Generated: jodo_v1_scaling_showcase_v2.pdf")

if __name__ == '__main__':
    generate_pdf()
