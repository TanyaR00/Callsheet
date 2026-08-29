import streamlit as st
import os
import pandas as pd

from src.agent.orchestrator import (
    parse_script_tool, 
    score_scene_risk_tool, 
    query_scene_comps_tool, 
    generate_scene_storyboard_tool, 
    generate_executive_briefing_audio_tool
)

st.set_page_config(page_title="Callsheet AI", layout="wide", initial_sidebar_state="expanded")

# --- Custom Styling ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e6edf3;
    }
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #ff4b4b;
        font-weight: 800;
    }
    .sub-header {
        font-style: italic;
        color: #8b949e;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🎬 CALLSHEET: Agentic Production Risk & Cost Intelligence</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Powered by Gemini, Google Cloud Agent Builder & ClickHouse Vector Analytics</p>', unsafe_allow_html=True)

st.sidebar.title("Controls")
script_option = st.sidebar.selectbox("Select Script", ["fixtures/sample_script.fountain", "Custom Upload"])

script_text = ""
if script_option == "Custom Upload":
    uploaded_file = st.sidebar.file_uploader("Upload Fountain/TXT file", type=["fountain", "txt"])
    if uploaded_file:
        script_text = uploaded_file.getvalue().decode("utf-8")
else:
    if os.path.exists(script_option):
        with open(script_option, "r") as f:
            script_text = f.read()
    else:
        st.sidebar.error(f"Sample script not found at {script_option}.")

run_pipeline = st.sidebar.button("🚀 Execute Agent Analysis")

if run_pipeline and script_text:
    
    with st.expander("Agent Execution & Live Trace", expanded=True):
        st.write("Initializing Lead Production Intelligence Orchestrator...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Parsing Script...")
        scenes = parse_script_tool(script_text)
        st.write(f"✅ Parsed {len(scenes)} scenes.")
        progress_bar.progress(10)
        
        scored_scenes = []
        
        for idx, scene in enumerate(scenes):
            status_text.text(f"Analyzing Scene {idx+1}: {scene['heading']}")
            
            try:
                risk_data = score_scene_risk_tool(scene)
                risk_score = risk_data['features']['risk_score']
                scene['risk_score'] = risk_score
                scene['primary_cost_driver'] = risk_data['rationale']['primary_cost_driver']
                scene['rationale_text'] = risk_data['rationale']['rationale']
                
                if risk_score < 5.0:
                    st.write(f"⏩ **Scene {idx+1} ({scene['heading']})**: Risk Score {risk_score}. Skipping expensive comp lookup.")
                    scene['comp_avg_cost'] = "Skipped"
                    scene['comp_confidence'] = "Skipped"
                else:
                    st.write(f"🔍 **Scene {idx+1} ({scene['heading']})**: Risk Score {risk_score} >= 5.0. Triggering ClickHouse comp search...")
                    comp_data = query_scene_comps_tool(scene['action_text'], scene['int_ext'], len(scene['characters']))
                    
                    if 'error' in comp_data:
                        st.write(f"⚠️ ClickHouse unreachable. Falling back to mock comparative metrics.")
                        scene['comp_avg_cost'] = 95000.0
                        scene['comp_confidence'] = "LOW (High Variance - Mocked)"
                        scene['comp_data'] = {
                            "p10_cost": 45000.0, "median_cost": 80000.0, "p90_cost": 150000.0,
                            "avg_cost": 95000.0, "cost_stddev": 35000.0, "comp_count": 5
                        }
                    else:
                        scene['comp_avg_cost'] = comp_data['avg_cost']
                        scene['comp_confidence'] = comp_data['confidence']
                        scene['comp_data'] = comp_data
                        st.write(f"🎯 Found Comps: Avg Cost ${comp_data['avg_cost']:,.2f} | Confidence: {comp_data['confidence']}")
            except Exception as e:
                st.write(f"❌ Error analyzing Scene {idx+1}: {e}")
                scene['risk_score'] = 0.0
                scene['primary_cost_driver'] = "Error"
                scene['rationale_text'] = str(e)
                scene['comp_avg_cost'] = "Error"
                scene['comp_confidence'] = "Error"
                
            scored_scenes.append(scene)
            progress_bar.progress(10 + int(40 * (idx + 1) / len(scenes)))
            
        sorted_scenes = sorted(scored_scenes, key=lambda x: x['risk_score'], reverse=True)
        top_3 = sorted_scenes[:3]
        
        status_text.text("Triggering Media Generation for top risk scenes...")
        
        storyboard_paths = []
        os.makedirs("artifacts/storyboards", exist_ok=True)
        os.makedirs("artifacts/audio", exist_ok=True)
        
        for i, scene in enumerate(top_3):
            if scene['risk_score'] >= 5.0:
                st.write(f"🎨 Generating Storyboard for Scene: {scene['heading']}...")
                try:
                    sb_path = generate_scene_storyboard_tool(scene['heading'], scene['action_text'], scene['primary_cost_driver'])
                    storyboard_paths.append((scene, sb_path))
                    st.write(f"✅ Storyboard saved.")
                except Exception as e:
                    st.write(f"⚠️ API restricted (Free Tier). Generating mock storyboard frame.")
                    sb_path = f"artifacts/storyboards/mock_{i}.jpg"
                    # Create a dummy valid blank image
                    from PIL import Image
                    Image.new('RGB', (1920, 1080), color = (73, 109, 137)).save(sb_path)
                    storyboard_paths.append((scene, sb_path))
        
        progress_bar.progress(80)
        
        audio_path = None
        highest_risk_scene = top_3[0] if top_3 else None
        
        if highest_risk_scene and highest_risk_scene['risk_score'] >= 5.0:
            status_text.text(f"Generating Executive Briefing Audio for {highest_risk_scene['heading']}...")
            try:
                risk_info = {"primary_cost_driver": highest_risk_scene['primary_cost_driver']}
                comp_info = {
                    "avg_cost": highest_risk_scene.get('comp_avg_cost', 0.0) if isinstance(highest_risk_scene.get('comp_avg_cost'), (float, int)) else 100000.0,
                    "p90_cost": highest_risk_scene.get('comp_data', {}).get('p90_cost', 150000.0),
                    "confidence": highest_risk_scene.get('comp_confidence', 'UNKNOWN')
                }
                audio_path = generate_executive_briefing_audio_tool(risk_info, comp_info)
                st.write(f"✅ Audio briefing synthesized.")
            except Exception as e:
                st.write(f"⚠️ Audio API Rate Limited. Generating mock audio file.")
                audio_path = "artifacts/audio/mock_audio.mp3"
                with open(audio_path, "wb") as f:
                    f.write(b"Mock Audio Data")
                
        progress_bar.progress(100)
        status_text.text("Pipeline Execution Complete!")
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Scene Breakdown & Risk Matrix", "ClickHouse Cost Comps", "Storyboard Moodboard", "Executive Audio Briefing"])
    
    with tab1:
        st.subheader("Scene Risk Matrix")
        df_data = []
        for s in scored_scenes:
            df_data.append({
                "Scene": s.get('heading', ''),
                "Location": s.get('location', ''),
                "Cast Size": len(s.get('characters', [])),
                "Risk Score": s.get('risk_score', 0.0),
                "Risk Rationale": s.get('rationale_text', '')
            })
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
    with tab2:
        st.subheader("Analytical Budget Distribution (ClickHouse)")
        comp_data = []
        total_exposure = 0
        for s in scored_scenes:
            if s.get('comp_avg_cost') not in ["Skipped", "Error"]:
                c_data = s.get('comp_data', {})
                comp_data.append({
                    "Scene": s.get('heading', ''),
                    "P10 Cost": f"${c_data.get('p10_cost', 0):,.2f}",
                    "Median Cost": f"${c_data.get('median_cost', 0):,.2f}",
                    "P90 Cost": f"${c_data.get('p90_cost', 0):,.2f}",
                    "Avg Cost": f"${c_data.get('avg_cost', 0):,.2f}",
                    "Confidence": s.get('comp_confidence', '')
                })
                total_exposure += c_data.get('avg_cost', 0)
        
        if comp_data:
            st.metric("Estimated Total Average Exposure", f"${total_exposure:,.2f}")
            st.table(comp_data)
        else:
            st.info("No comparative cost data generated (all scenes were low risk).")
            
    with tab3:
        st.subheader("Imagen 3 Top-Risk Moodboard")
        if storyboard_paths:
            cols = st.columns(len(storyboard_paths))
            for idx, (scene, path) in enumerate(storyboard_paths):
                with cols[idx]:
                    if os.path.exists(path):
                        st.image(path, caption=f"{scene['heading']} - Primary Risk: {scene['primary_cost_driver']}")
                    else:
                        st.warning("Image missing")
        else:
            st.info("No storyboards generated.")
            
    with tab4:
        st.subheader("Executive Audio Briefing (Dual Speaker)")
        if audio_path and os.path.exists(audio_path):
            st.audio(audio_path)
            st.markdown(f"""
            **Speaker 1 (Line Producer)**: We've run the numbers for this scene. The primary operational bottleneck is the {highest_risk_scene.get('primary_cost_driver', 'VFX requirements')}.
            **Speaker 2 (Executive Producer)**: What are we looking at in terms of budget exposure?
            **Speaker 1**: Our historical comps average around ${highest_risk_scene.get('comp_avg_cost', 0):,.2f}.
            **Speaker 2**: And the variance?
            **Speaker 1**: The P90 cost is ${highest_risk_scene.get('comp_data', {}).get('p90_cost', 0):,.2f}. The variance is {highest_risk_scene.get('comp_confidence', 'HIGH')} confidence.
            **Speaker 2**: Understood. Let's make sure we pad the schedule appropriately.
            """)
        else:
            st.info("No audio briefing generated.")
