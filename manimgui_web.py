import os
import re
import subprocess
from pathlib import Path

import streamlit as st


QUALITY_FLAGS = {
    "📱 Low (480p)": "-ql",
    "💻 High (1080p)": "-qh",
    "🎥 4K (2160p)": "-qk",
    "🖼️ Medium (720p)": "-qm",
}

OUTPUT_FLAGS = {
    "🎬 MP4 Video": [],
    "🖼️ PNG Image": ["-s"],
    "📐 SVG Vector": ["-s", "--format=svg"],
}


def detect_scene_classes(code: str):
    pattern = r"class\s+(\w+)\(.*Scene.*\)"
    return re.findall(pattern, code)


def list_py_files(project_dir: Path):
    if not project_dir.exists():
        return []
  codex/improve-logging-system-and-ui-wjiw0z
 
  codex/improve-logging-system-and-ui-gcwvxn
   main
    files = []
    for path in project_dir.rglob("*.py"):
        if path.is_file():
            files.append(str(path.relative_to(project_dir)))
    return sorted(files)


def update_from_github(repo_dir: Path):
    git_dir = repo_dir / ".git"
    if not os.path.isdir(git_dir):
        return False, "No git repository found next to the app files."

    update = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
    )
    output = "\n".join(x for x in [update.stdout.strip(), update.stderr.strip()] if x).strip()
    if not output:
        output = "No output from git."
    return update.returncode == 0, output
  codex/improve-logging-system-and-ui-wjiw0z


def deep_repo_scan(repo_dir: Path):
    """Scan repository files for unresolved merge markers."""
    markers = ("<<<<<<<", "=======", ">>>>>>>")
    flagged = []
    for pattern in ("*.py", "*.md", "*.txt", "*.yml", "*.yaml"):
        for file_path in repo_dir.rglob(pattern):
            if ".git" in file_path.parts:
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if any(marker in content for marker in markers):
                flagged.append(str(file_path.relative_to(repo_dir)))
    return sorted(flagged)
 
 
    return sorted([str(p.relative_to(project_dir)) for p in project_dir.glob("*.py")])
  main
  main


def build_manim_command(file_path: Path, scene_class: str, quality_label: str, output_label: str):
    cmd = ["manim", QUALITY_FLAGS.get(quality_label, "-qh")]
    cmd.extend(OUTPUT_FLAGS.get(output_label, []))
    if output_label == "🎬 MP4 Video":
        cmd.append("-p")
    cmd.extend([str(file_path), scene_class])
    return cmd


def append_log(line: str):
    st.session_state.logs.append(line.rstrip("\n"))


def filtered_logs():
    level = st.session_state.log_filter
    logs = st.session_state.logs
    if level == "Info Only":
        return [line for line in logs if "INFO" in line or "✅" in line or "▶️" in line]
    if level == "Warnings+":
        return [line for line in logs if "WARNING" in line or "ERROR" in line or "⚠️" in line or "❌" in line]
    if level == "Errors Only":
        return [line for line in logs if "ERROR" in line or "❌" in line or "Exception" in line]
    return logs


def render_scene(project_dir: Path, file_path: Path, scene_class: str, quality_label: str, output_label: str):
    cmd = build_manim_command(file_path, scene_class, quality_label, output_label)
    st.session_state.logs = []
    st.session_state.last_output_file = ""
    st.session_state.last_output_dir = ""
    append_log(f"▶️ Starting render: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        cwd=str(project_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    log_box = st.empty()
    for line in process.stdout:
        append_log(line)
        ready_match = re.search(r"File ready at:\s*(.*\.(mp4|png|svg))", line)
        if ready_match:
            relative_path = ready_match.group(1).strip()
            absolute_output = (project_dir / relative_path).resolve()
            st.session_state.last_output_file = str(absolute_output)
            st.session_state.last_output_dir = str(absolute_output.parent)
            append_log(f"🎥 Output ready: {absolute_output}")

        log_box.code("\n".join(filtered_logs()) or "No logs yet.", language="bash")

    process.wait()
    if process.returncode == 0:
        append_log("✅ Render completed successfully.")
    else:
        append_log(f"❌ Render failed with exit code {process.returncode}.")

    log_box.code("\n".join(filtered_logs()) or "No logs yet.", language="bash")


def main():
    st.set_page_config(page_title="Manim Web Studio", page_icon="🎬", layout="wide")
    st.title("🎬 Manim Web Studio")
    st.caption("A web-based Manim editor with improved logs, render controls, and output navigation.")

    if "logs" not in st.session_state:
        st.session_state.logs = []
    if "last_output_file" not in st.session_state:
        st.session_state.last_output_file = ""
    if "last_output_dir" not in st.session_state:
        st.session_state.last_output_dir = ""
    if "log_filter" not in st.session_state:
        st.session_state.log_filter = "All Logs"

    with st.sidebar:
        st.header("⚙️ Project")
        project_dir_str = st.text_input("Project directory", value=str(Path.cwd()))
        project_dir = Path(project_dir_str).expanduser().resolve()

  codex/improve-logging-system-and-ui-wjiw0z
 
  codex/improve-logging-system-and-ui-gcwvxn
  main
        if st.button("🔄 Update from GitHub", use_container_width=True):
            repo_dir = Path(__file__).resolve().parent
            ok, output = update_from_github(repo_dir)
            if ok:
                st.success("Update completed. Restart Streamlit if needed.")
            else:
                st.error("Update failed. Check output below.")
            st.code(output, language="bash")

  codex/improve-logging-system-and-ui-wjiw0z
        if st.button("🔍 Deep Error Scan", use_container_width=True):
            repo_dir = Path(__file__).resolve().parent
            conflict_files = deep_repo_scan(repo_dir)
            if conflict_files:
                st.error("Found unresolved merge markers:")
                st.code("\n".join(conflict_files), language="bash")
            else:
                st.success("Deep scan complete: no merge conflict markers found.")

 
 
  main
  main
        py_files = list_py_files(project_dir)
        selected_file = st.selectbox("Python file", options=py_files if py_files else [""])
        st.session_state.log_filter = st.selectbox(
            "Log filter", ["All Logs", "Info Only", "Warnings+", "Errors Only"], index=0
        )

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("🧠 Scene Editor")
        if selected_file:
            file_path = project_dir / selected_file
            source = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
        else:
            file_path = project_dir / "scene.py"
            source = ""

        code = st.text_area("Code", value=source, height=480)
        scenes = detect_scene_classes(code)
        default_scene = scenes[0] if scenes else ""
        scene_class = st.text_input("Scene class", value=default_scene)

        q_col, o_col, s_col = st.columns(3)
        with q_col:
            quality = st.selectbox("Quality", list(QUALITY_FLAGS.keys()))
        with o_col:
            output_type = st.selectbox("Output", list(OUTPUT_FLAGS.keys()))
        with s_col:
            st.write("")
            st.write("")
            save_clicked = st.button("💾 Save File", use_container_width=True)

        if save_clicked:
            project_dir.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code, encoding="utf-8")
            st.success(f"Saved: {file_path}")

        render_clicked = st.button("▶️ Render Scene", type="primary", use_container_width=True)
        if render_clicked:
            if not scene_class.strip():
                st.error("Please enter a scene class.")
            else:
                project_dir.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code, encoding="utf-8")
                render_scene(project_dir, file_path, scene_class.strip(), quality, output_type)

    with right:
        st.subheader("📊 Logs")
        shown_logs = "\n".join(filtered_logs())
        st.code(shown_logs or "No logs yet.", language="bash")
        st.download_button(
            "💾 Download Logs",
            data=(shown_logs + "\n") if shown_logs else "",
            file_name="manim_render_logs.txt",
            use_container_width=True,
        )

        st.subheader("📁 Output")
        if st.session_state.last_output_file:
            st.text_input("Last output file", st.session_state.last_output_file)
        else:
            st.info("No output generated yet.")

        if st.session_state.last_output_dir:
            st.text_input("Output folder", st.session_state.last_output_dir)


if __name__ == "__main__":
    main()
