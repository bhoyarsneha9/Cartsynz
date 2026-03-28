import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from tracker import (
    load_alerts_for, add_alert, remove_alert, update_alert,
    check_cart_expiry, days_left_in_cart,
    get_price_with_tinyfish, get_product_info_with_tinyfish,
    add_to_cart_with_tinyfish, login_with_tinyfish,
    scrape_deals_parallel, load_deals, save_deals,
    get_user, upsert_user,
    generate_otp, verify_otp,
    send_sms_otp, send_sms_cart_alert,
    SITE_LOGIN_URLS,
)

# ─── ENV ──────────────────────────────────────────────────────────────────────
API_KEY      = os.getenv("TINYFISH_API_KEY", "")
TWILIO_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE = os.getenv("TWILIO_PHONE", "")

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CARTSYNCZ",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { font-family: 'DM Sans', sans-serif; }

:root {
    --bg:        #06060f;
    --surface:   #0d0d1a;
    --border:    #1a1a2e;
    --border2:   #252540;
    --text:      #e2e2f0;
    --muted:     #50506a;
    --accent1:   #9d7cfc;
    --accent2:   #5aa4f5;
    --accent3:   #34d399;
    --danger:    #f87171;
    --warn:      #fbbf24;
}

.stApp { background: var(--bg); color: var(--text); }
.main .block-container { padding: 0 2rem 5rem 2rem; max-width: 1240px; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }

/* ─── NAVBAR ─── */
.navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 0 16px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
}
.brand-logo {
    font-family: 'Syne', sans-serif;
    font-size: 27px;
    font-weight: 800;
    background: linear-gradient(125deg, #c084fc, #60a5fa 50%, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
}
.brand-tag {
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-top: -2px;
}
.nav-pills { display: flex; gap: 6px; }
.nav-pill {
    padding: 7px 16px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 500;
    border: 1px solid var(--border);
    color: var(--muted);
    background: transparent;
    cursor: pointer;
    transition: all 0.2s;
}
.nav-pill.active {
    background: linear-gradient(125deg, #9d7cfc18, #5aa4f518);
    border-color: #9d7cfc55;
    color: #c4b5fd;
}

/* ─── BUTTONS ─── */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stMultiSelect"] > div > div {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: border-color 0.2s !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent1) !important;
    box-shadow: 0 0 0 3px #9d7cfc18 !important;
}
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    border: 1px solid var(--border2) !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    border-color: #9d7cfc66 !important;
    background: #12122a !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px #9d7cfc18 !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(125deg, #7c3aed, #3b82f6) !important;
    border-color: transparent !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.92 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px #7c3aed44 !important;
}
.stButton > button[kind="primary"]:active {
    opacity: 1 !important;
    transform: translateY(0) !important;
}
div[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
}

/* ─── CARDS ─── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s, transform 0.25s, box-shadow 0.25s;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #9d7cfc33, transparent);
}
.card:hover {
    border-color: #9d7cfc33;
    transform: translateY(-2px);
    box-shadow: 0 12px 40px #9d7cfc0c;
}

/* ─── DEAL CARDS ─── */
.deal-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 20px; }
.deal-card {
    background: linear-gradient(145deg, var(--surface), #110f1f);
    border: 1px solid #221a38;
    border-radius: 20px;
    padding: 0;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
}
.deal-card:hover {
    border-color: #9d7cfc88;
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 20px 60px #9d7cfc1a;
}
.deal-card:active { transform: translateY(-2px) scale(1.01); }
.deal-img-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    overflow: hidden;
    background: linear-gradient(135deg, #1a1a2e, #0f0f20);
}
.deal-img-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.5s ease;
    display: block;
}
.deal-card:hover .deal-img-wrap img { transform: scale(1.08); }
.deal-img-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 52px;
    background: linear-gradient(135deg, #13102a, #0e0e1c);
}
.deal-discount-badge {
    position: absolute;
    top: 10px; left: 10px;
    background: linear-gradient(125deg, #16a34a, #15803d);
    color: white;
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 100px;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 12px #16a34a44;
}
.deal-store-badge {
    position: absolute;
    top: 10px; right: 10px;
    background: #060610cc;
    backdrop-filter: blur(8px);
    color: #60a5fa;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 100px;
    border: 1px solid #1e3050;
}
.deal-body { padding: 14px 16px 16px 16px; }
.deal-name {
    font-size: 13.5px;
    font-weight: 600;
    color: #c0c0d8;
    line-height: 1.45;
    margin-bottom: 10px;
    min-height: 38px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.deal-prices {
    display: flex;
    align-items: baseline;
    gap: 8px;
    flex-wrap: wrap;
}
.deal-price-current {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: var(--accent1);
}
.deal-price-orig {
    font-size: 13px;
    color: var(--muted);
    text-decoration: line-through;
}

/* ─── BADGES ─── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 600;
}
.badge-site  { background: #0f1d35; color: #60a5fa; border: 1px solid #1e3050; }
.badge-deal  { background: #0f2a1a; color: #4ade80; border: 1px solid #1a3a20; }
.badge-cart  { background: #2e1a1a; color: #f87171; border: 1px solid #3e2020; }
.badge-hit   { background: #221640; color: #c4b5fd; border: 1px solid #3a2a60; }
.badge-warn  { background: #2a1e00; color: #fbbf24; border: 1px solid #3a2e00; }

/* ─── PRICES ─── */
.price-current {
    font-family: 'Syne', sans-serif;
    font-size: 30px;
    font-weight: 700;
    color: var(--accent1);
    line-height: 1;
}
.price-range { font-size: 13px; color: var(--muted); margin-top: 4px; }

/* ─── TICKER ─── */
.ticker-wrap {
    overflow: hidden;
    background: linear-gradient(90deg, var(--bg), var(--surface), var(--bg));
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 10px 0;
    margin-bottom: 28px;
}
.ticker-inner {
    display: flex;
    gap: 56px;
    animation: ticker 35s linear infinite;
    white-space: nowrap;
    width: max-content;
}
@keyframes ticker {
    0%   { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
.ticker-item { font-size: 13px; color: #666; display: inline-flex; align-items: center; gap: 8px; }

/* ─── MISC ─── */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 5px;
}
.section-sub { font-size: 14px; color: var(--muted); margin-bottom: 22px; }
.vdivider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 26px 0;
}
.timer-bar-wrap {
    background: #1a1a2e;
    border-radius: 100px;
    height: 5px;
    margin-top: 8px;
    overflow: hidden;
}
.timer-bar {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, var(--danger), var(--warn));
}
.auth-wrap { max-width: 420px; margin: 60px auto; }
.auth-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 40px 36px;
}
.auth-title {
    font-family: 'Syne', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 8px;
    text-align: center;
}
.auth-sub { font-size: 14px; color: var(--muted); text-align: center; margin-bottom: 28px; }

/* ─── HERO ─── */
.hero {
    text-align: center;
    padding: 52px 0 40px 0;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(38px, 6.5vw, 70px);
    font-weight: 800;
    line-height: 1.06;
    background: linear-gradient(125deg, #ffffff 0%, #a78bfa 55%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 18px;
}
.hero-sub {
    color: var(--muted);
    font-size: 17px;
    max-width: 500px;
    margin: 0 auto 36px auto;
    line-height: 1.65;
}

/* ─── TOP DEAL BANNER ─── */
.top-deal-banner {
    background: linear-gradient(135deg, #12101e, #1a1030);
    border: 1px solid #9d7cfc22;
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.top-deal-banner::after {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, #9d7cfc0a, transparent 70%);
    pointer-events: none;
}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border2); }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
for key, default in {
    "page": "home",
    "auth_step": "phone",
    "auth_phone": "",
    "user": None,
    "site_sessions": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── API KEY CHECK ─────────────────────────────────────────────────────────────
if not API_KEY:
    st.error("⚠️  Add TINYFISH_API_KEY to your .env file and restart.")
    st.stop()

# ─── NAVBAR ───────────────────────────────────────────────────────────────────
pages = [
    ("🏠", "Home",    "home"),
    ("🎯", "Alerts",  "alerts"),
    ("🔥", "Deals",   "deals"),
    ("🛒", "Cart",    "cart"),
    ("⚙️", "Account", "account"),
]

nav_pills = "".join(
    f'<div class="nav-pill {"active" if st.session_state.page == pid else ""}">{icon} {label}</div>'
    for icon, label, pid in pages
)
st.markdown(
    f'<div class="navbar">'
    f'<div><div class="brand-logo">CARTSYNCZ</div>'
    f'<div class="brand-tag">Smart Shopping Automation</div></div>'
    f'<div class="nav-pills">{nav_pills}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# Functional nav buttons — always rendered, hidden visually behind the HTML nav
nav_cols = st.columns(len(pages))
for i, (icon, label, pid) in enumerate(pages):
    with nav_cols[i]:
        if st.button(f"{icon} {label}", key=f"nav_{pid}", use_container_width=True):
            st.session_state.page = pid
            st.rerun()

st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)


# ─── AUTH ─────────────────────────────────────────────────────────────────────
def render_auth():
    st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="auth-card">
        <div class="auth-title">👋 Welcome to CARTSYNCZ</div>
        <div class="auth-sub">Sign in with your phone to get started</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth_step == "phone":
        phone = st.text_input("Phone Number", placeholder="+91 98765 43210", key="input_phone")
        if st.button("Send OTP via SMS 📲", type="primary", use_container_width=True):
            phone = phone.strip().replace(" ", "")
            if not phone.startswith("+"):
                st.warning("Include country code, e.g. +91…")
            else:
                otp = generate_otp(phone)
                if TWILIO_SID and TWILIO_TOKEN and TWILIO_PHONE:
                    ok = send_sms_otp(phone, otp, TWILIO_SID, TWILIO_TOKEN, TWILIO_PHONE)
                    if ok:
                        st.session_state.auth_phone = phone
                        st.session_state.auth_step  = "otp"
                        st.success("✅ OTP sent via SMS!")
                        st.rerun()
                    else:
                        st.error("Could not send SMS. Check Twilio credentials in .env")
                else:
                    st.session_state.auth_phone = phone
                    st.session_state.auth_step  = "otp"
                    st.info(f"🔧 Dev mode — OTP: **{otp}**")
                    st.rerun()

    elif st.session_state.auth_step == "otp":
        st.info(f"OTP sent to {st.session_state.auth_phone}")
        otp_input = st.text_input("Enter 6-digit OTP", max_chars=6, placeholder="123456", key="input_otp")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Verify OTP ✅", type="primary", use_container_width=True):
                if verify_otp(st.session_state.auth_phone, otp_input):
                    user = upsert_user(st.session_state.auth_phone, last_login=datetime.now().isoformat())
                    st.session_state.user      = user
                    st.session_state.auth_step = "done"
                    st.success("Logged in! 🎉")
                    st.rerun()
                else:
                    st.error("Wrong or expired OTP. Try again.")
        with c2:
            if st.button("← Change Number", use_container_width=True):
                st.session_state.auth_step = "phone"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


protected = ["alerts", "cart", "account"]
if st.session_state.page in protected and not st.session_state.user:
    render_auth()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "home":

    st.markdown("""
    <div class="hero">
        <div class="hero-title">Shop Smarter.<br>Buy at the Right Price.</div>
        <div class="hero-sub">
            CARTSYNCZ watches prices across every shopping site.
            When your price drops — we add it to cart and send you an SMS.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    features = [
        ("🌐", "Any Website",  "Amazon, Flipkart, Myntra, Meesho, Nykaa and thousands more."),
        ("📱", "SMS Alerts",   "Instant SMS when your price target is hit and item is added."),
        ("🤖", "AI‑Powered",   "TinyFish AI browses and shops for you — fully automated."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], features):
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center; padding:32px 24px;">
                <div style="font-size:38px; margin-bottom:14px;">{icon}</div>
                <div style="font-family:'Syne',sans-serif; font-size:17px; font-weight:700;
                            color:var(--text); margin-bottom:8px;">{title}</div>
                <div style="font-size:14px; color:var(--muted); line-height:1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)

    cola, colb = st.columns(2)
    with cola:
        if st.button("🎯 Set Price Alert", type="primary", use_container_width=True):
            st.session_state.page = "alerts"
            st.rerun()
    with colb:
        if st.button("🔥 Browse Deals", use_container_width=True):
            st.session_state.page = "deals"
            st.rerun()

    # How it works
    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="text-align:center; margin-bottom:24px;">How it works</div>', unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    steps = [
        ("1", "Paste URL", "Any product from any site"),
        ("2", "Set Range", "Your min & max target price"),
        ("3", "We Watch", "TinyFish checks prices 24/7"),
        ("4", "Auto Cart", "Price drops → added + SMS"),
    ]
    for col, (num, title, desc) in zip([s1, s2, s3, s4], steps):
        with col:
            st.markdown(f"""
            <div style="text-align:center; padding:20px 12px;">
                <div style="width:40px; height:40px; border-radius:50%;
                            background:linear-gradient(125deg,#7c3aed,#3b82f6);
                            display:inline-flex; align-items:center; justify-content:center;
                            font-family:'Syne',sans-serif; font-size:16px; font-weight:800;
                            color:white; margin-bottom:12px;">{num}</div>
                <div style="font-family:'Syne',sans-serif; font-size:15px; font-weight:700;
                            color:var(--text); margin-bottom:6px;">{title}</div>
                <div style="font-size:13px; color:var(--muted); line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ALERTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "alerts":

    phone = st.session_state.user["phone"]

    st.markdown('<div class="section-title">🎯 Add Price Alert</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Paste any product URL — from any shopping site.</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        new_url = st.text_input(
            "Product URL",
            placeholder="https://amazon.in/dp/...  or  https://myntra.com/...",
            key="new_url",
        )

        col_site, col_min, col_max = st.columns([2, 1, 1])
        with col_site:
            site_options = list(SITE_LOGIN_URLS.keys())
            new_site = st.selectbox("Shopping Site", site_options, key="new_site")
            if new_site == "Other":
                custom_site = st.text_input("Enter site name", placeholder="e.g. Croma", key="custom_site")
                if custom_site:
                    new_site = custom_site
        with col_min:
            min_price = st.number_input("Min Price (₹)", min_value=0.0, value=500.0, step=50.0, key="min_price")
        with col_max:
            max_price = st.number_input("Max Price (₹)", min_value=1.0, value=1500.0, step=50.0, key="max_price")

        st.markdown(f"""
        <div style="font-size:13px; color:var(--muted); margin:8px 0 16px 0;">
            Auto-add to cart when price is between
            <span style="color:#c4b5fd; font-weight:600;">₹{min_price:,.0f}</span> and
            <span style="color:#c4b5fd; font-weight:600;">₹{max_price:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Set Alert 🎯", type="primary", use_container_width=True, key="btn_set_alert"):
            if not new_url.strip():
                st.warning("Please paste a product URL.")
            elif min_price >= max_price:
                st.warning("Max price must be greater than min price.")
            else:
                with st.spinner("Fetching product info via TinyFish AI…"):
                    info = get_product_info_with_tinyfish(new_url.strip(), API_KEY)
                alert = add_alert(phone, new_url.strip(), new_site, min_price, max_price)
                if info.get("price"):
                    history = [{"price": info["price"], "at": datetime.now().isoformat()}]
                    update_alert(
                        alert["id"],
                        current_price=info["price"],
                        product_name=info.get("name", ""),
                        product_image=info.get("image", ""),
                        price_history=history,
                    )
                st.success(f"✅ Alert set! Watching for ₹{min_price:,.0f} – ₹{max_price:,.0f}")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # Site Login
    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    with st.expander("🔐 Connect Shopping Accounts"):
        st.markdown('<div style="font-size:14px; color:var(--muted); margin-bottom:16px;">Log in once — CARTSYNCZ auto-adds to cart when price drops.</div>', unsafe_allow_html=True)

        all_sites = [s for s in SITE_LOGIN_URLS.keys() if s != "Other"]
        l_site = st.selectbox("Select Site", all_sites, key="l_site")
        l_url  = SITE_LOGIN_URLS.get(l_site, "")
        if not l_url:
            l_url = st.text_input("Login page URL", key="l_custom_url")

        l_email = st.text_input("Email / Username", key="l_email")
        l_pass  = st.text_input("Password", type="password", key="l_pass")

        if st.button("Log In & Save Session 🔑", type="primary", use_container_width=True, key="btn_login_site"):
            if not l_email or not l_pass:
                st.warning("Enter your credentials.")
            else:
                with st.spinner(f"TinyFish AI logging into {l_site}… (30–90 sec)"):
                    ok, token, reason = login_with_tinyfish(l_site, l_email, l_pass, API_KEY, l_url)
                if ok:
                    st.session_state.site_sessions[l_site] = token
                    st.success(f"✅ Connected to {l_site}!")
                else:
                    st.error(f"❌ {reason}")

        if st.session_state.site_sessions:
            st.markdown("**Connected:**")
            for s in st.session_state.site_sessions:
                st.markdown(f'<span class="badge badge-site">✅ {s}</span>&nbsp;', unsafe_allow_html=True)

    # Alert Cards
    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)

    alerts = load_alerts_for(phone)
    for a in alerts:
        if check_cart_expiry(a):
            update_alert(a["id"], in_cart=False, cart_added_at=None)
    alerts = load_alerts_for(phone)

    if not alerts:
        st.markdown("""
        <div style="text-align:center; padding:60px 0; color:#2a2a3e;">
            <div style="font-size:50px;">📭</div>
            <div style="font-size:16px; margin-top:12px; color:var(--muted);">
                No alerts yet. Add your first product above!
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-title">📋 Your Alerts ({len(alerts)})</div>', unsafe_allow_html=True)

        for alert in reversed(alerts):
            aid     = alert["id"]
            min_p   = alert["min_price"]
            max_p   = alert["max_price"]
            current = alert.get("current_price")
            in_cart = alert.get("in_cart", False)
            site    = alert.get("site", "")
            url     = alert["url"]
            name    = alert.get("product_name", "") or url[:55] + "…"
            image   = alert.get("product_image", "")
            history = alert.get("price_history", [])
            price_in_range = current is not None and min_p <= current <= max_p
            short_url = url if len(url) <= 50 else url[:47] + "…"

            st.markdown('<div class="card">', unsafe_allow_html=True)
            col_img, col_info, col_act = st.columns([1, 3, 2])

            with col_img:
                if image:
                    st.markdown(
                        f'<div style="border-radius:14px; overflow:hidden; aspect-ratio:1;">'
                        f'<img src="{image}" style="width:100%;height:100%;object-fit:cover;"/></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div style="border-radius:14px; aspect-ratio:1; background:linear-gradient(135deg,#1a1a2e,#0f0f20);\
                        display:flex; align-items:center; justify-content:center; font-size:38px;">🛍️</div>',
                        unsafe_allow_html=True,
                    )

            with col_info:
                st.markdown(f'<span class="badge badge-site">{site}</span>', unsafe_allow_html=True)
                st.markdown(
                    f'<div style="font-size:15px; font-weight:600; color:var(--text); margin:8px 0 4px 0; line-height:1.4;">{name}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="font-size:12px; margin-bottom:10px;">'
                    f'<a href="{url}" target="_blank" style="color:var(--muted); text-decoration:none;">{short_url} ↗</a>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if current:
                    price_color = "#4ade80" if price_in_range else "var(--accent1)"
                    st.markdown(f'<div class="price-current" style="color:{price_color};">₹{current:,.0f}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="color:var(--muted); font-size:14px;">Price not checked yet</div>', unsafe_allow_html=True)

                st.markdown(f'<div class="price-range">Target: ₹{min_p:,.0f} – ₹{max_p:,.0f}</div>', unsafe_allow_html=True)

                if price_in_range:
                    st.markdown('<span class="badge badge-hit">🎉 Price in range!</span>', unsafe_allow_html=True)

                if in_cart:
                    days = days_left_in_cart(alert)
                    pct  = (days / 7) * 100 if days else 0
                    st.markdown(f"""
                    <span class="badge badge-cart" style="margin-top:6px; display:inline-flex;">🛒 In cart · {days}d left</span>
                    <div class="timer-bar-wrap"><div class="timer-bar" style="width:{pct}%;"></div></div>
                    """, unsafe_allow_html=True)

                if len(history) > 1:
                    import pandas as pd
                    df = pd.DataFrame(history)
                    df["at"] = pd.to_datetime(df["at"])
                    st.line_chart(df.set_index("at")["price"], height=60, use_container_width=True)

            with col_act:
                if st.button("🔍 Check Price", key=f"chk_{aid}", use_container_width=True):
                    with st.spinner("TinyFish AI checking price…"):
                        fetched = get_price_with_tinyfish(url, API_KEY)
                    if fetched is not None:
                        h = history + [{"price": fetched, "at": datetime.now().isoformat()}]
                        update_alert(aid, current_price=fetched, price_history=h)
                        st.success(f"₹{fetched:,.0f}")
                        st.rerun()
                    else:
                        st.error("Could not fetch price.")

                if price_in_range and not in_cart:
                    if st.button("🛒 Add to Cart", key=f"cart_{aid}", use_container_width=True, type="primary"):
                        sess = st.session_state.site_sessions.get(site, "")
                        if not sess:
                            st.warning(f"Connect your {site} account first ↑")
                        else:
                            with st.spinner("TinyFish AI adding to cart…"):
                                ok, reason = add_to_cart_with_tinyfish(url, site, API_KEY)
                            if ok:
                                update_alert(aid, in_cart=True, cart_added_at=datetime.now().isoformat())
                                if TWILIO_SID and TWILIO_TOKEN and TWILIO_PHONE:
                                    send_sms_cart_alert(
                                        phone, name, current, site,
                                        TWILIO_SID, TWILIO_TOKEN, TWILIO_PHONE,
                                    )
                                st.success("✅ Added to cart! SMS sent.")
                                st.rerun()
                            else:
                                st.error(f"❌ {reason}")

                if st.button("🗑️ Remove", key=f"del_{aid}", use_container_width=True):
                    remove_alert(aid)
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DEALS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "deals":

    st.markdown('<div class="section-title">🔥 Top Price Drops Today</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Biggest discounts across popular shopping sites — powered by TinyFish AI</div>', unsafe_allow_html=True)

    ticker_items = [
        "Amazon 🔥 Up to 70% off Electronics",
        "Flipkart 🛒 Fashion sale live",
        "Myntra 👗 Min 50% off",
        "Meesho 💚 Prices drop every hour",
        "Nykaa 💄 Buy 2 Get 1 Free",
        "Ajio 👟 Sneakers at lowest ever",
    ]
    ticker_html = '<div class="ticker-wrap"><div class="ticker-inner">'
    for item in ticker_items * 2:
        ticker_html += f'<div class="ticker-item">🟢 {item}</div>'
    ticker_html += '</div></div>'
    st.markdown(ticker_html, unsafe_allow_html=True)

    deal_sites = {
        "Amazon.in": "https://www.amazon.in/deals",
        "Flipkart":  "https://www.flipkart.com/offers-store",
        "Myntra":    "https://www.myntra.com/offers",
        "Meesho":    "https://www.meesho.com",
        "Nykaa":     "https://www.nykaa.com/offers",
    }

    selected_sites = st.multiselect(
        "Pick sites to scan for deals",
        list(deal_sites.keys()),
        default=["Amazon.in", "Flipkart"],
        key="deal_sites_select",
    )

    col_btn, col_note = st.columns([2, 3])
    with col_btn:
        scan_clicked = st.button(
            "🤖 Scan for Best Deals with TinyFish AI",
            type="primary",
            use_container_width=True,
            key="btn_scan_deals",
        )
    with col_note:
        if len(selected_sites) > 1:
            st.markdown(
                f'<div style="font-size:13px; color:var(--muted); padding-top:10px;">'
                f'⚡ Scanning {len(selected_sites)} sites in parallel — '
                f'~{len(selected_sites) * 30}s max (vs {len(selected_sites) * 90}s sequential)</div>',
                unsafe_allow_html=True,
            )

    if scan_clicked:
        if not selected_sites:
            st.warning("Please select at least one site.")
        else:
            with st.spinner(f"TinyFish AI scanning {len(selected_sites)} site(s) in parallel…"):
                site_map = {s: deal_sites[s] for s in selected_sites}
                all_deals = scrape_deals_parallel(site_map, API_KEY, max_deals=3)
            save_deals(all_deals)
            st.rerun()

    deals = load_deals()

    if not deals:
        st.markdown("""
        <div style="text-align:center; padding:70px 0; color:#1a1a2e;">
            <div style="font-size:52px;">🔍</div>
            <div style="font-size:16px; margin-top:14px; color:var(--muted);">
                Click the button above to scan for today's best deals!
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Top deal banner ──────────────────────────────────────────────
        top = max(deals, key=lambda d: d.get("discount_pct") or 0)
        top_img = top.get("image", "")
        top_url = top.get("url", "#")

        banner_img_html = (
            f'<img src="{top_img}" style="width:140px; height:140px; border-radius:16px; '
            f'object-fit:cover; flex-shrink:0; border:1px solid #9d7cfc22;"/>'
            if top_img else
            '<div style="width:140px; height:140px; border-radius:16px; background:linear-gradient(135deg,#1a1a2e,#0f0f20);\
            display:flex; align-items:center; justify-content:center; font-size:52px; flex-shrink:0;">🛍️</div>'
        )

        st.markdown(f"""
        <div class="top-deal-banner">
            <div style="display:flex; gap:24px; align-items:center; flex-wrap:wrap;">
                {banner_img_html}
                <div style="flex:1; min-width:200px;">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px; flex-wrap:wrap;">
                        <span class="badge badge-deal">🏆 TOP DEAL</span>
                        <span class="badge badge-site">{top.get('store','')}</span>
                    </div>
                    <div style="font-family:'Syne',sans-serif; font-size:20px; font-weight:700;
                                color:var(--text); margin-bottom:12px; line-height:1.3;">
                        {top.get('name','Product')[:80]}
                    </div>
                    <div style="display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;">
                        <div style="font-family:'Syne',sans-serif; font-size:30px; font-weight:800; color:#4ade80;">
                            ↓ {top.get('discount_pct',0):.0f}% OFF
                        </div>
                        <div style="font-size:26px; color:var(--accent1); font-weight:700;">
                            ₹{top.get('price',0):,.0f}
                        </div>
                        <div style="font-size:16px; color:var(--muted); text-decoration:line-through;">
                            ₹{top.get('original_price',0):,.0f}
                        </div>
                    </div>
                    <a href="{top_url}" target="_blank"
                       style="display:inline-block; margin-top:14px; font-size:13px;
                              color:var(--accent1); text-decoration:none;">
                        View on {top.get('store','')} ↗
                    </a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Deal grid — interactive image cards ─────────────────────────
        st.markdown(
            '<div class="section-title" style="margin-top:8px; margin-bottom:4px;">All Deals</div>',
            unsafe_allow_html=True,
        )

        # Build deal cards HTML + track which deal each alert-button corresponds to
        cards_html = '<div class="deal-grid">'
        for i, deal in enumerate(deals):
            name  = (deal.get("name") or "Product")[:60]
            price = deal.get("price") or 0
            orig  = deal.get("original_price") or 0
            disc  = deal.get("discount_pct") or 0
            store = deal.get("store", "")
            img   = deal.get("image", "")
            durl  = deal.get("url", "#")

            img_html = (
                f'<img src="{img}" alt="{name}" '
                f'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';" />'
                f'<div class="deal-img-placeholder" style="display:none;">🛍️</div>'
                if img else
                '<div class="deal-img-placeholder">🛍️</div>'
            )

            disc_badge = f'<span class="deal-discount-badge">-{disc:.0f}%</span>' if disc else ""
            orig_html  = f'<span class="deal-price-orig">₹{orig:,.0f}</span>' if orig else ""

            cards_html += f"""
            <a href="{durl}" target="_blank" style="text-decoration:none;" class="deal-card" id="deal-card-{i}">
                <div class="deal-img-wrap">
                    {img_html}
                    {disc_badge}
                    <span class="deal-store-badge">{store}</span>
                </div>
                <div class="deal-body">
                    <div class="deal-name">{name}</div>
                    <div class="deal-prices">
                        <span class="deal-price-current">₹{price:,.0f}</span>
                        {orig_html}
                    </div>
                </div>
            </a>
            """
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

        # ── "Set Alert" buttons below grid (one per deal) ───────────────
        st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
        n_cols = 3
        rows   = [deals[i : i + n_cols] for i in range(0, len(deals), n_cols)]
        for row_idx, row in enumerate(rows):
            btn_cols = st.columns(n_cols)
            for col_idx, deal in enumerate(row):
                global_idx = row_idx * n_cols + col_idx
                with btn_cols[col_idx]:
                    dname  = (deal.get("name") or "Product")[:30]
                    dprice = deal.get("price") or 0
                    durl   = deal.get("url", "#")
                    dstore = deal.get("store", "")
                    if st.button(f"🎯 Set Alert — {dname}…", key=f"deal_alert_{global_idx}", use_container_width=True):
                        if st.session_state.user:
                            add_alert(
                                st.session_state.user["phone"],
                                durl, dstore,
                                dprice * 0.88,   # target 12% below current
                                dprice,
                            )
                            st.success(f"Alert set for ₹{dprice * 0.88:,.0f} – ₹{dprice:,.0f}!")
                        else:
                            st.session_state.page = "alerts"
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CART
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "cart":

    phone  = st.session_state.user["phone"]
    alerts = [a for a in load_alerts_for(phone) if a.get("in_cart")]

    st.markdown('<div class="section-title">🛒 Items in Cart</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Items auto-added by CARTSYNCZ. They expire after 7 days.</div>', unsafe_allow_html=True)

    if not alerts:
        st.markdown("""
        <div style="text-align:center; padding:70px 0; color:#1a1a2e;">
            <div style="font-size:52px;">🛒</div>
            <div style="font-size:16px; margin-top:14px; color:var(--muted);">
                Your cart is empty. Set alerts and let CARTSYNCZ fill it!
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎯 Set an Alert", type="primary", use_container_width=False, key="btn_go_alerts"):
            st.session_state.page = "alerts"
            st.rerun()
    else:
        for a in alerts:
            days = days_left_in_cart(a)
            pct  = (days / 7) * 100 if days else 0
            name = a.get("product_name", "") or a["url"][:50]
            img  = a.get("product_image", "")

            st.markdown('<div class="card">', unsafe_allow_html=True)
            ci, cd = st.columns([1, 4])
            with ci:
                if img:
                    st.markdown(
                        f'<div style="border-radius:14px;overflow:hidden;aspect-ratio:1;">'
                        f'<img src="{img}" style="width:100%;height:100%;object-fit:cover;"/></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div style="border-radius:14px;aspect-ratio:1;background:linear-gradient(135deg,#1a1a2e,#0f0f20);\
                        display:flex;align-items:center;justify-content:center;font-size:32px;">🛍️</div>',
                        unsafe_allow_html=True,
                    )
            with cd:
                st.markdown(f'<span class="badge badge-site">{a.get("site","")}</span>', unsafe_allow_html=True)
                st.markdown(
                    f'<div style="font-size:16px; font-weight:600; color:var(--text); margin:8px 0 4px 0;">{name}</div>',
                    unsafe_allow_html=True,
                )
                cp = a.get("current_price", 0) or 0
                st.markdown(f'<div class="price-current">₹{cp:,.0f}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<span class="badge badge-cart" style="margin-top:8px;">🛒 {days} days left</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="timer-bar-wrap" style="width:220px; margin-top:8px;">'
                    f'<div class="timer-bar" style="width:{pct}%;"></div></div>',
                    unsafe_allow_html=True,
                )
                c_view, c_remove = st.columns([2, 1])
                with c_view:
                    st.markdown(
                        f'<a href="{a["url"]}" target="_blank" style="font-size:13px; color:var(--accent1); text-decoration:none;">View item ↗</a>',
                        unsafe_allow_html=True,
                    )
                with c_remove:
                    if st.button("Remove", key=f"cart_remove_{a['id']}", use_container_width=True):
                        update_alert(a["id"], in_cart=False, cart_added_at=None)
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ACCOUNT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "account":

    user  = st.session_state.user
    phone = user["phone"]

    st.markdown('<div class="section-title">⚙️ Account</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div style="display:flex; align-items:center; gap:18px;">
            <div style="width:58px; height:58px; border-radius:50%;
                        background:linear-gradient(125deg,#7c3aed,#3b82f6);
                        display:flex; align-items:center; justify-content:center;
                        font-size:24px; flex-shrink:0;">👤</div>
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:19px;
                            font-weight:700; color:var(--text);">{phone}</div>
                <div style="font-size:13px; color:var(--muted); margin-top:3px;">
                    Member since {user.get('created_at','')[:10]}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    all_alerts = load_alerts_for(phone)
    active  = [a for a in all_alerts if not a.get("in_cart")]
    in_cart = [a for a in all_alerts if a.get("in_cart")]

    c1, c2, c3 = st.columns(3)
    for col, label, val, icon in [
        (c1, "Active Alerts", len(active),     "🎯"),
        (c2, "In Cart",       len(in_cart),    "🛒"),
        (c3, "Total Tracked", len(all_alerts), "📊"),
    ]:
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:30px; margin-bottom:8px;">{icon}</div>
                <div style="font-family:'Syne',sans-serif; font-size:30px;
                            font-weight:800; color:var(--accent1);">{val}</div>
                <div style="font-size:13px; color:var(--muted);">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔗 Connected Sites</div>', unsafe_allow_html=True)

    if st.session_state.site_sessions:
        for s in list(st.session_state.site_sessions.keys()):
            col_s, col_b = st.columns([4, 1])
            with col_s:
                st.markdown(f'<span class="badge badge-site">✅ {s}</span>', unsafe_allow_html=True)
            with col_b:
                if st.button("Disconnect", key=f"disc_{s}", use_container_width=True):
                    del st.session_state.site_sessions[s]
                    st.rerun()
    else:
        st.markdown('<div style="color:var(--muted); font-size:14px;">No sites connected yet.</div>', unsafe_allow_html=True)

    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📱 SMS Alerts</div>', unsafe_allow_html=True)
    if TWILIO_SID and TWILIO_TOKEN and TWILIO_PHONE:
        st.markdown('<span class="badge badge-deal">✅ Twilio SMS Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-warn">⚠️ Twilio not configured — add to .env</span>', unsafe_allow_html=True)

    st.markdown('<div class="vdivider"></div>', unsafe_allow_html=True)

    col_logout, _ = st.columns([1, 2])
    with col_logout:
        if st.button("🚪 Log Out", use_container_width=True, key="btn_logout"):
            st.session_state.user      = None
            st.session_state.auth_step = "phone"
            st.session_state.page      = "home"
            st.rerun()


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:48px 0 12px 0; color:#1e1e35; font-size:12px;
            font-family:'DM Sans',sans-serif; letter-spacing:1px;">
    CARTSYNCZ · Powered by TinyFish AI 🐟 · Built for TinyFish Hackathon
</div>
""", unsafe_allow_html=True)
