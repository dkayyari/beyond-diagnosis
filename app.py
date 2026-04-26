import streamlit as st
import pandas as pd
import pymysql

st.set_page_config(
    page_title="Beyond Diagnosis — HIV Support System",
    page_icon="❤️",
    layout="wide"
)

def run_query(sql):
    try:
        conn = pymysql.connect(
            host="shortline.proxy.rlwy.net",
            port=36258,
            user="root",
            password="ZJPPtOprIWCdIcLrwSTYcynzzbJLRXQR",
            database="railway"
        )
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

# ── Global CSS
st.markdown("""
<style>
    .stApp { background-color: #F8FBFF; }
    h2 { color: #0D8A8A !important; }
    h3 { color: #1A3A5C !important; }
    .profile-card {
        background: linear-gradient(135deg, #1A3A5C, #0D8A8A);
        border-radius: 12px;
        padding: 16px;
        color: white;
        text-align: center;
        margin-bottom: 12px;
    }
    .profile-name { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
    .profile-role { font-size: 12px; opacity: 0.85; }
    .profile-stage {
        font-size: 12px;
        background: rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 3px 10px;
        margin-top: 6px;
        display: inline-block;
    }
    .welcome-banner {
        background: linear-gradient(135deg, #E8F5F5, #EFF6FF);
        border-left: 5px solid #0D8A8A;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    .welcome-title { font-size: 20px; font-weight: 700; color: #1A3A5C; margin-bottom: 4px; }
    .welcome-msg { font-size: 14px; color: #4A5568; }
    .badge-completed { background:#D1FAE5; color:#065F46; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-missed    { background:#FEE2E2; color:#991B1B; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-scheduled { background:#FEF3C7; color:#92400E; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)




if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role      = None
    st.session_state.user_id   = None

# ── Demo credentials
CREDENTIALS = {
    "patient":   {"password": "patient123",   "role": "Patient"},
    "doctor":    {"password": "doctor123",     "role": "Doctor"},
    "therapist": {"password": "therapist123",  "role": "Therapist"},
}

def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## ❤️ Beyond Diagnosis")
        st.markdown("#### HIV Patient Support System")
        st.markdown("---")
        username = st.text_input("Username:", placeholder="e.g. patient, doctor, therapist")
        password = st.text_input("Password:", type="password", placeholder="Enter your password")
        user_id_input = st.text_input("Enter your ID:", placeholder="e.g. 1, 25, 100")
        if st.button("🔐 Login", use_container_width=True):
            username = username.strip().lower()
            if username not in CREDENTIALS:
                st.error("❌ Invalid username. Use: patient, doctor, or therapist.")
                st.stop()
            if password != CREDENTIALS[username]["password"]:
                st.error("❌ Incorrect password.")
                st.stop()
            role = CREDENTIALS[username]["role"]
            try:
                user_id = int(user_id_input.strip())
            except ValueError:
                st.error("❌ Please enter a valid numeric ID.")
                st.stop()
            if role == "Patient":
                df = run_query(f"SELECT patient_id FROM patient WHERE patient_id = {user_id}")
            elif role == "Doctor":
                df = run_query(f"SELECT doctor_id FROM doctor WHERE doctor_id = {user_id}")
            else:
                df = run_query(f"SELECT therapist_id FROM therapist WHERE therapist_id = {user_id}")
            if not df.empty:
                st.session_state.logged_in = True
                st.session_state.role      = role
                st.session_state.user_id   = user_id
                st.rerun()
            else:
                st.error(f"❌ {role} ID {user_id} not found. Try 1–200 for patients, 1–15 for doctors/therapists.")
        st.markdown("---")
        st.caption("Demo credentials — Patient: `patient` / `patient123` | Doctor: `doctor` / `doctor123` | Therapist: `therapist` / `therapist123`")

def patient_dashboard(patient_id):
    df_patient = run_query(f"""
        SELECT p.patient_id, p.anon_alias, p.age_range, p.gender_identity,
               p.registration_date,
               SUBSTRING_INDEX(cs.stage_name, ' (', 1) AS stage_name,
               cs.cd4_range, cs.intervention_level, cs.description
        FROM patient p
        JOIN care_stage cs ON p.current_stage_id = cs.care_stage_id
        WHERE p.patient_id = {patient_id}
    """)
    if df_patient.empty:
        st.error("Patient not found.")
        return
    row = df_patient.iloc[0]
    st.markdown(f"""
    <div class="welcome-banner">
        <div class="welcome-title">👤 Welcome back, {row['anon_alias']}!</div>
        <div class="welcome-msg">Every day you show up for your health is a victory. Here is your care summary.</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Age Range",  row['age_range'])
    c2.metric("Gender",     row['gender_identity'])
    c3.metric("Care Stage", row['stage_name'])
    c4.metric("CD4 Range",  row['cd4_range'])

    st.info(f"🏥 Intervention Level: {row['intervention_level']}")
    st.markdown(f"📋 {str(row['description'])}")
    st.markdown("---")

    # ── Positive Wellness Card
    st.markdown("### 💚 Your Progress — You Are Doing Amazing!")

    df_fu_all = run_query(f"SELECT status FROM followup_instance WHERE patient_id = {patient_id}")
    df_ts_all = run_query(f"SELECT session_date FROM therapy_session WHERE patient_id = {patient_id}")
    df_ep_all = run_query(f"SELECT completion_status FROM education_progress WHERE patient_id = {patient_id}")
    df_reg    = run_query(f"SELECT registration_date FROM patient WHERE patient_id = {patient_id}")

    total_visits  = len(df_fu_all)
    kept_visits   = len(df_fu_all[df_fu_all['status'] == 'Completed']) if not df_fu_all.empty else 0
    therapy_count = len(df_ts_all)
    total_modules = len(df_ep_all)
    done_modules  = len(df_ep_all[df_ep_all['completion_status'] == 'Completed']) if not df_ep_all.empty else 0

    days_in_care = 0
    if not df_reg.empty:
        import datetime
        reg = pd.to_datetime(df_reg.iloc[0]['registration_date'])
        days_in_care = (datetime.datetime.today() - reg).days

    visit_pct = int((kept_visits / total_visits * 100)) if total_visits > 0 else 0
    edu_pct   = int((done_modules / total_modules * 100)) if total_modules > 0 else 0

    if visit_pct >= 75:
        visit_msg = f"Outstanding! You attended {kept_visits} of {total_visits} appointments."
    elif visit_pct >= 50:
        visit_msg = f"Great effort! You attended {kept_visits} of {total_visits} appointments."
    else:
        visit_msg = f"Keep going! You attended {kept_visits} of {total_visits} appointments."

    if done_modules >= 5:
        edu_msg = f"Incredible! You completed {done_modules} education modules — knowledge is power!"
    elif done_modules >= 2:
        edu_msg = f"Nice work! You completed {done_modules} modules — keep learning!"
    else:
        edu_msg = f"Great start! You completed {done_modules} modules so far."

    if therapy_count >= 10:
        therapy_msg = f"Fantastic! You attended {therapy_count} therapy sessions — investing in your wellbeing!"
    elif therapy_count >= 5:
        therapy_msg = f"Well done! You attended {therapy_count} therapy sessions."
    else:
        therapy_msg = f"You attended {therapy_count} therapy sessions — every session counts!"

    w1, w2, w3, w4 = st.columns(4)
    w1.success(f"🎯 Appointments\n\n{visit_msg}\n\n{visit_pct}% kept")
    w2.success(f"📚 Learning Journey\n\n{edu_msg}\n\n{edu_pct}% complete")
    w3.success(f"🧠 Therapy\n\n{therapy_msg}")
    w4.success(f"❤️ Days in Care\n\nYou have been actively managing your health for {days_in_care} days. That takes real strength!")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📅 Follow-Up History")
        df_fu = run_query(f"""
            SELECT followup_date, visit_type, status, notes
            FROM followup_instance
            WHERE patient_id = {patient_id}
            ORDER BY followup_date DESC LIMIT 10
        """)
        if not df_fu.empty:
            def highlight_status(row):
                if row['status'] == 'Completed':
                    return ['background-color: #EAFAF1'] * len(row)
                elif row['status'] == 'Missed':
                    return ['background-color: #FDEDEC'] * len(row)
                else:
                    return ['background-color: #FEF9E7'] * len(row)
            st.dataframe(df_fu.style.apply(highlight_status, axis=1), use_container_width=True, height=280)
        else:
            st.info("No follow-up records found.")

    with col2:
        st.markdown("### 🧠 Therapy Sessions")
        df_ts = run_query(f"""
            SELECT session_date, modality, outcome, session_notes
            FROM therapy_session
            WHERE patient_id = {patient_id}
            ORDER BY session_date DESC LIMIT 10
        """)
        if not df_ts.empty:
            st.dataframe(df_ts, use_container_width=True, height=280)
        else:
            st.info("No therapy sessions found.")

    st.markdown("---")
    st.markdown("### 📚 Education Progress")
    df_ep = run_query(f"""
        SELECT er.title, er.category, er.format,
               ep.completion_status, ep.self_rating, ep.access_date
        FROM education_progress ep
        JOIN education_resource er ON ep.resource_id = er.resource_id
        WHERE ep.patient_id = {patient_id}
        ORDER BY ep.access_date DESC
    """)
    if not df_ep.empty:
        total     = len(df_ep)
        completed = len(df_ep[df_ep['completion_status'] == 'Completed'])
        pct       = completed / total if total > 0 else 0
        st.progress(pct, text=f"✅ {completed} of {total} modules completed ({pct*100:.0f}%)")
        st.dataframe(df_ep, use_container_width=True, height=250)
    else:
        st.info("No education records found.")


    st.markdown("---")
    st.markdown("### 🛡️ My Prevention Strategies")
    df_pp = run_query(f"SELECT ps.strategy_name, ps.target_population, pp.enrollment_date, pp.adherence_status FROM patient_prevention pp JOIN prevention_strategy ps ON pp.strategy_id = ps.strategy_id WHERE pp.patient_id = {patient_id} ORDER BY pp.enrollment_date DESC")
    if not df_pp.empty:
        st.caption("Your currently enrolled prevention strategies:")
        st.dataframe(df_pp, use_container_width=True)
    else:
        st.info("No prevention strategies enrolled.")

    stage_strategy_map = {
        "Acute HIV Infection":                      ["HIV Testing & Status Awareness", "Condom Use & Barrier Methods", "Partner Services & Contact Notification"],
        "Chronic HIV Infection (Clinical Latency)": ["ART — Treatment as Prevention (TasP)", "U=U (Undetectable = Untransmittable)", "HIV Testing & Status Awareness"],
        "Symptomatic HIV Infection":                ["ART — Treatment as Prevention (TasP)", "Mental Health & Psychosocial Support", "U=U (Undetectable = Untransmittable)"],
        "AIDS (Advanced HIV Disease)":              ["ART — Treatment as Prevention (TasP)", "Mental Health & Psychosocial Support", "Syringe Services Programs (SSP)"],
        "Virally Suppressed (On ART)":              ["U=U (Undetectable = Untransmittable)", "ART — Treatment as Prevention (TasP)", "Mental Health & Psychosocial Support"],
    }
    df_stage_full = run_query(f"SELECT cs.stage_name FROM patient p JOIN care_stage cs ON p.current_stage_id = cs.care_stage_id WHERE p.patient_id = {patient_id}")
    if not df_stage_full.empty:
        full_stage = df_stage_full.iloc[0]['stage_name']
        recommended = None
        for key in stage_strategy_map:
            if key.lower() in full_stage.lower() or full_stage.lower() in key.lower():
                recommended = stage_strategy_map[key]
                break
        if not recommended:
            recommended = ["ART — Treatment as Prevention (TasP)", "HIV Testing & Status Awareness", "Mental Health & Psychosocial Support"]
        st.markdown("#### 💡 Recommended for Your Care Stage")
        st.caption("Based on your current care stage, these strategies are commonly recommended:")
        names_sql = ", ".join([f"'{s}'" for s in recommended])
        df_rec = run_query(f"SELECT strategy_name, description, target_population FROM prevention_strategy WHERE strategy_name IN ({names_sql})")
        if not df_rec.empty:
            for _, r in df_rec.iterrows():
                with st.expander(f"✅ {r['strategy_name']}"):
                    st.write(r['description'])
                    st.caption(f"Target population: {r['target_population']}")


def clinician_dashboard(doctor_id):
    st.markdown("## 🏥 Clinician Dashboard")
    df_doc = run_query(f"SELECT specialization, organization, years_experience FROM doctor WHERE doctor_id = {doctor_id}")
    if not df_doc.empty:
        d = df_doc.iloc[0]
        st.markdown(f"**Specialization:** {d['specialization']}  |  **Organization:** {d['organization']}  |  **Experience:** {d['years_experience']} years")
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Total Patients",   run_query("SELECT COUNT(*) AS n FROM patient").iloc[0]['n'])
    c2.metric("⚠️ Missed Visits",    run_query("SELECT COUNT(*) AS n FROM followup_instance WHERE status = 'Missed'").iloc[0]['n'])
    c3.metric("✅ Completed Visits", run_query("SELECT COUNT(*) AS n FROM followup_instance WHERE status = 'Completed'").iloc[0]['n'])
    c4.metric("🧠 Therapy Sessions", run_query("SELECT COUNT(*) AS n FROM therapy_session").iloc[0]['n'])
    st.markdown("---")
    st.markdown("### ⚠️ Missed Visit Alerts — Top 10 Patients")
    df_missed = run_query("""
        SELECT p.patient_id, CONCAT('Patient #', p.patient_id) AS patient_ref, p.age_range,
               cs.stage_name, COUNT(*) AS missed_visits
        FROM followup_instance fi
        JOIN patient p     ON fi.patient_id      = p.patient_id
        JOIN care_stage cs ON p.current_stage_id = cs.care_stage_id
        WHERE fi.status = 'Missed'
        GROUP BY p.patient_id, patient_ref, p.age_range, cs.stage_name
        ORDER BY missed_visits DESC LIMIT 10
    """)
    if not df_missed.empty:
        st.dataframe(df_missed, use_container_width=True, height=280)
    st.markdown("---")
    st.markdown("### 👥 All Patients Overview")
    search = st.text_input("🔍 Search by alias or care stage:", "")
    df_all = run_query("""
        SELECT p.patient_id, CONCAT('Patient #', p.patient_id) AS patient_ref, p.age_range, p.gender_identity,
               cs.stage_name,
               COUNT(DISTINCT fi.followup_date) AS total_visits,
               SUM(CASE WHEN fi.status = 'Missed'    THEN 1 ELSE 0 END) AS missed,
               SUM(CASE WHEN fi.status = 'Completed' THEN 1 ELSE 0 END) AS completed
        FROM patient p
        LEFT JOIN care_stage cs        ON p.current_stage_id = cs.care_stage_id
        LEFT JOIN followup_instance fi ON p.patient_id       = fi.patient_id
        GROUP BY p.patient_id, patient_ref, p.age_range, p.gender_identity, cs.stage_name
        ORDER BY missed DESC
    """)
    if search:
        df_all = df_all[
            df_all['patient_ref'].str.contains(search, case=False, na=False) |
            df_all['stage_name'].str.contains(search, case=False, na=False)
        ]
    st.dataframe(df_all, use_container_width=True, height=350)
    st.markdown("---")
    st.markdown("### 📊 Care Stage Distribution")
    df_stages = run_query("""
        SELECT cs.stage_name, COUNT(*) AS patient_count
        FROM patient p
        JOIN care_stage cs ON p.current_stage_id = cs.care_stage_id
        GROUP BY cs.stage_name ORDER BY patient_count DESC
    """)
    if not df_stages.empty:
        st.bar_chart(df_stages.set_index('stage_name')['patient_count'])

def therapist_dashboard(therapist_id):
    st.markdown("## 🧠 Therapist Dashboard")
    df_th = run_query(f"SELECT therapy_type, organization, license_type FROM therapist WHERE therapist_id = {therapist_id}")
    if not df_th.empty:
        t = df_th.iloc[0]
        st.markdown(f"**Therapy Type:** {t['therapy_type']}  |  **Organization:** {t['organization']}  |  **License:** {t['license_type']}")
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("📋 Total Sessions",    run_query(f"SELECT COUNT(*) AS n FROM therapy_session WHERE therapist_id = {therapist_id}").iloc[0]['n'])
    c2.metric("✅ Improved Outcomes", run_query(f"SELECT COUNT(*) AS n FROM therapy_session WHERE therapist_id = {therapist_id} AND outcome = 'Improved'").iloc[0]['n'])
    c3.metric("👥 Patients Seen",     run_query(f"SELECT COUNT(DISTINCT patient_id) AS n FROM therapy_session WHERE therapist_id = {therapist_id}").iloc[0]['n'])
    st.markdown("---")
    st.markdown("### 📋 My Sessions")
    df_sessions = run_query(f"""
        SELECT ts.session_date, CONCAT('Patient #', p.patient_id) AS patient_ref, ts.modality, ts.outcome, ts.session_notes
        FROM therapy_session ts
        JOIN patient p ON ts.patient_id = p.patient_id
        WHERE ts.therapist_id = {therapist_id}
        ORDER BY ts.session_date DESC LIMIT 20
    """)
    if not df_sessions.empty:
        st.dataframe(df_sessions, use_container_width=True, height=350)
    else:
        st.info("No sessions found.")
    st.markdown("---")
    st.markdown("### 📊 Outcome Distribution")
    df_outcomes = run_query(f"""
        SELECT outcome, COUNT(*) AS count FROM therapy_session
        WHERE therapist_id = {therapist_id}
        GROUP BY outcome ORDER BY count DESC
    """)
    if not df_outcomes.empty:
        st.bar_chart(df_outcomes.set_index('outcome')['count'])

def education_hub(role="Patient"):
    st.markdown("## 📚 Education & Prevention Hub")
    st.markdown("---")

    if role == "Patient":
        # ── Patient: browse CDC education modules
        st.markdown("### 🔍 Browse Education Resources")
        st.caption("CDC and NIH approved health education materials for HIV patients.")
        df_res = run_query("SELECT title, category, format, stage_target, source_url FROM education_resource ORDER BY category, title")
        if not df_res.empty:
            categories = ["All"] + sorted(df_res['category'].dropna().unique().tolist())
            selected   = st.selectbox("Filter by category:", categories)
            df_show    = df_res if selected == "All" else df_res[df_res['category'] == selected]
            st.dataframe(df_show, use_container_width=True, height=300)
        st.markdown("---")
        st.markdown("### 🛡️ HIV Prevention Strategies")
        st.caption("Evidence-based prevention strategies recommended by the CDC.")
        df_prev = run_query("SELECT strategy_name, target_population, source_guideline FROM prevention_strategy ORDER BY strategy_name")
        st.dataframe(df_prev, use_container_width=True)

    elif role == "Doctor":
        # ── Clinician: OI reference + clinical guidelines + prevention
        st.markdown("### 🔬 Opportunistic Infection Clinical Reference")
        st.caption("Source: DHHS Guidelines for Prevention and Treatment of OIs in Adults with HIV, May 2024.")
        df_oi = run_query("SELECT oi_name, cd4_threshold, prophylaxis_rec, first_line_drug, alternative_drug, monitoring_interval FROM oi_reference ORDER BY cd4_threshold")
        st.dataframe(df_oi, use_container_width=True)
        st.markdown("---")
        st.markdown("### 💊 Care Stage Clinical Interventions")
        st.caption("Recommended intervention levels per HIV care stage.")
        df_cs = run_query("SELECT stage_name, cd4_range, intervention_level, description FROM care_stage ORDER BY care_stage_id")
        st.dataframe(df_cs, use_container_width=True)
        st.markdown("---")
        st.markdown("### 🛡️ Prevention Strategy Reference")
        st.caption("CDC evidence-based prevention strategies with source guidelines.")
        df_prev = run_query("SELECT strategy_name, description, target_population, source_guideline FROM prevention_strategy ORDER BY strategy_name")
        st.dataframe(df_prev, use_container_width=True)
        st.markdown("---")
        st.markdown("### 📋 Clinical Education Resources")
        st.caption("Clinical and provider-facing education materials.")
        df_clin = run_query("SELECT title, category, format, source_url FROM education_resource WHERE category IN ('Treatment','Clinical/OI','Testing','Prevention') ORDER BY category, title")
        st.dataframe(df_clin, use_container_width=True, height=250)

    elif role == "Therapist":
        # ── Therapist: mental health + psychosocial resources
        st.markdown("### 🧠 Mental Health & Psychosocial Resources")
        st.caption("Resources focused on mental health, stigma, and psychosocial support for HIV patients.")
        df_mh = run_query("SELECT title, category, format, source_url FROM education_resource WHERE category IN ('Mental Health','Stigma / Data','Living with HIV','Basic Education') ORDER BY category, title")
        st.dataframe(df_mh, use_container_width=True, height=300)
        st.markdown("---")
        st.markdown("### 🤝 Therapy Modality Reference")
        st.caption("Overview of therapy types used in HIV psychosocial care.")
        therapy_data = {
            "Modality": ["Cognitive Behavioral Therapy (CBT)", "Group Therapy", "Motivational Interviewing", "Mindfulness-Based Therapy", "Occupational Therapy", "Speech Therapy", "Physical Therapy", "Hydrotherapy"],
            "Primary Use": ["Adherence, depression, anxiety", "Peer support, reducing isolation", "Medication adherence, behavior change", "Stress management, anxiety", "Functional recovery, daily living", "Communication, neurological symptoms", "Physical rehabilitation", "Pain management, relaxation"],
            "Recommended For": ["All stages", "Chronic & Symptomatic stages", "Non-adherent patients", "High anxiety patients", "AIDS & Symptomatic stages", "Neurological complications", "Physical complications", "Symptomatic & AIDS stages"]
        }
        import pandas as pd
        st.dataframe(pd.DataFrame(therapy_data), use_container_width=True)
        st.markdown("---")
        st.markdown("### 🛡️ Prevention Strategies — Psychosocial Focus")
        df_prev = run_query("SELECT strategy_name, description, target_population FROM prevention_strategy WHERE strategy_name IN ('Mental Health & Psychosocial Support','U=U (Undetectable = Untransmittable)','HIV Testing & Status Awareness','Partner Services & Contact Notification') ORDER BY strategy_name")
        st.dataframe(df_prev, use_container_width=True)

if not st.session_state.logged_in:
    login_screen()
else:
    with st.sidebar:
        # Profile card
        role_icon = {"Patient": "👤", "Doctor": "🏥", "Therapist": "🧠"}.get(st.session_state.role, "👤")
        st.markdown(f"""
        <div class="profile-card">
            <div style="font-size:32px">{role_icon}</div>
            <div class="profile-name">ID: {st.session_state.user_id}</div>
            <div class="profile-role">{st.session_state.role}</div>
            <div class="profile-stage">❤️ Beyond Diagnosis</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        if st.session_state.role == "Patient":
            page = st.radio("Navigate:", ["🏠 My Dashboard", "📚 Education Hub"])
        elif st.session_state.role == "Doctor":
            page = st.radio("Navigate:", ["🏥 Clinician Dashboard", "📚 Education Hub"])
        else:
            page = st.radio("Navigate:", ["🧠 My Sessions", "📚 Education Hub"])
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role      = None
            st.session_state.user_id   = None
            st.rerun()

    if st.session_state.role == "Patient":
        if page == "🏠 My Dashboard":
            patient_dashboard(st.session_state.user_id)
        else:
            education_hub(role="Patient")
    elif st.session_state.role == "Doctor":
        if page == "🏥 Clinician Dashboard":
            clinician_dashboard(st.session_state.user_id)
        else:
            education_hub(role="Doctor")
    else:
        if page == "🧠 My Sessions":
            therapist_dashboard(st.session_state.user_id)
        else:
            education_hub(role="Therapist")
