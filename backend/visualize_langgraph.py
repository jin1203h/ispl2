"""
LangGraph 워크플로우 시각화 도구
PDF 처리 워크플로우를 그래프로 시각화합니다.
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from agents.supervisor import SupervisorAgent
    from langgraph.graph import StateGraph
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import networkx as nx
    
    # 한글 폰트 설정
    import platform
    if platform.system() == 'Windows':
        # Windows 시스템에서 한글 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False
    else:
        # 다른 시스템에서는 기본 한글 폰트 시도
        font_list = [font.name for font in fm.fontManager.ttflist if 'korean' in font.name.lower() or 'malgun' in font.name.lower() or 'nanum' in font.name.lower()]
        if font_list:
            plt.rcParams['font.family'] = font_list[0]
        else:
            # 한글 폰트를 찾을 수 없는 경우 기본 설정
            plt.rcParams['font.family'] = 'DejaVu Sans'
    
    VISUALIZATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 시각화 라이브러리 가져오기 실패: {e}")
    print("다음 명령으로 필요한 라이브러리를 설치하세요:")
    print("pip install matplotlib networkx")
    VISUALIZATION_AVAILABLE = False

def visualize_workflow_graph():
    """LangGraph 워크플로우를 시각화합니다."""
    
    if not VISUALIZATION_AVAILABLE:
        return
    
    try:
        # SupervisorAgent 초기화
        supervisor = SupervisorAgent()
        
        # 워크플로우 그래프 가져오기
        if supervisor.workflow is None:
            print("❌ 워크플로우가 생성되지 않았습니다.")
            return
        
        print("🎨 LangGraph 워크플로우 시각화 중...")
        
        # NetworkX 그래프 생성
        G = nx.DiGraph()
        
        # 노드 정의 (워크플로우 단계)
        nodes = [
            ("pdf_analysis", "PDF Analysis"),
            ("text_extraction", "Text Extraction"),
            ("table_extraction", "Table Extraction"),
            ("image_ocr", "Image OCR"),
            ("markdown_conversion", "Markdown Conversion"),
            ("embedding_generation", "Embedding Generation"),
            ("finalize", "Finalize")
        ]
        
        # 노드 추가
        for node_id, node_label in nodes:
            G.add_node(node_id, label=node_label)
        
        # 엣지 정의 (워크플로우 연결)
        edges = [
            ("pdf_analysis", "text_extraction"),
            ("text_extraction", "table_extraction"),
            ("table_extraction", "image_ocr"),
            ("image_ocr", "markdown_conversion"),
            ("markdown_conversion", "embedding_generation"),
            ("embedding_generation", "finalize")
        ]
        
        # 엣지 추가
        G.add_edges_from(edges)
        
        # 그래프 시각화 설정
        plt.figure(figsize=(14, 10))
        plt.title("PDF Processing Workflow (LangGraph)", fontsize=16, fontweight='bold', pad=20)
        
        # 레이아웃 설정 (계층적 배치)
        pos = {
            "pdf_analysis": (0, 5),
            "text_extraction": (-2, 4),
            "table_extraction": (0, 3),
            "image_ocr": (2, 2),
            "markdown_conversion": (0, 1),
            "embedding_generation": (0, 0),
            "finalize": (0, -1)
        }
        
        # 노드 색상 설정
        node_colors = {
            "pdf_analysis": "#FF6B6B",      # Red (Start)
            "text_extraction": "#4ECDC4",   # Teal
            "table_extraction": "#45B7D1",  # Blue
            "image_ocr": "#96CEB4",         # Green
            "markdown_conversion": "#FECA57", # Yellow
            "embedding_generation": "#FF9FF3", # Pink
            "finalize": "#54A0FF"           # Purple (End)
        }
        
        # 노드 그리기
        for node in G.nodes():
            nx.draw_networkx_nodes(
                G, pos, 
                nodelist=[node],
                node_color=node_colors.get(node, '#CCCCCC'),
                node_size=3000,
                alpha=0.8
            )
        
        # 엣지 그리기
        nx.draw_networkx_edges(
            G, pos,
            edge_color='#666666',
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            width=2,
            alpha=0.7
        )
        
        # 라벨 그리기
        labels = {node_id: data['label'] for node_id, data in G.nodes(data=True)}
        nx.draw_networkx_labels(
            G, pos, labels,
            font_size=10,
            font_weight='bold',
            font_color='white'
        )
        
        # 범례 추가
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B', markersize=10, label='Start Stage'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#4ECDC4', markersize=10, label='Extraction Stage'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FECA57', markersize=10, label='Conversion Stage'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#54A0FF', markersize=10, label='Final Stage')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # 축 제거 및 여백 설정
        plt.axis('off')
        plt.tight_layout()
        
        # 이미지 저장
        output_file = "langgraph_workflow_visualization.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        print(f"✅ Workflow graph saved to '{output_file}'.")
        
        # 그래프 표시 (GUI 환경에서)
        try:
            plt.show()
        except:
            print("💡 Cannot display graph in non-GUI environment.")
            print(f"   Please check the saved file: {output_file}")
        
    except Exception as e:
        print(f"❌ Visualization error: {e}")

def print_workflow_structure():
    """Print workflow structure in text format."""
    
    print("\n" + "="*60)
    print("📊 LangGraph Workflow Structure")
    print("="*60)
    
    workflow_steps = [
        ("1. PDF Analysis", "pdf_analysis", "Read PDF file and extract metadata"),
        ("2. Text Extraction", "text_extraction", "Extract text content from PDF"),
        ("3. Table Extraction", "table_extraction", "Extract table data from PDF"),
        ("4. Image OCR", "image_ocr", "Extract text from images"),
        ("5. Markdown Conversion", "markdown_conversion", "Convert extracted content to Markdown"),
        ("6. Embedding Generation", "embedding_generation", "Generate text embedding vectors"),
        ("7. Finalize", "finalize", "Organize and save processing results")
    ]
    
    for step_name, node_id, description in workflow_steps:
        print(f"\n{step_name}")
        print(f"   Node ID: {node_id}")
        print(f"   Description: {description}")
        
        # 다음 단계 표시
        next_steps = {
            "pdf_analysis": ["text_extraction"],
            "text_extraction": ["table_extraction"],
            "table_extraction": ["image_ocr"],
            "image_ocr": ["markdown_conversion"],
            "markdown_conversion": ["embedding_generation"],
            "embedding_generation": ["finalize"],
            "finalize": []
        }
        
        if next_steps.get(node_id):
            print(f"   → Next: {', '.join(next_steps[node_id])}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("🎨 LangGraph Workflow Visualization Tool")
    print("="*50)
    
    # 텍스트 구조 출력
    print_workflow_structure()
    
    # 그래프 시각화
    if VISUALIZATION_AVAILABLE:
        visualize_workflow_graph()
    else:
        print("\n💡 Please install required libraries for graph visualization:")
        print("   pip install matplotlib networkx")
