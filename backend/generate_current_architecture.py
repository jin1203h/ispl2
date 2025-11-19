"""
현재 구현된 ISPL2 시스템의 아키텍처 다이어그램 생성
실제 구현 상황을 반영한 정확한 시각화
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import matplotlib.font_manager as fm

# 한글 폰트 설정
import platform
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False

def create_current_architecture_diagram():
    """현재 구현된 시스템의 아키텍처 다이어그램 생성"""
    
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 14)
    ax.axis('off')
    
    # 색상 정의
    colors = {
        'frontend': '#2196F3',      # 파란색
        'backend': '#4CAF50',       # 초록색
        'agents': '#FF5722',        # 주황색
        'database': '#9C27B0',      # 보라색
        'external': '#FF9800',      # 오렌지색
        'monitoring': '#607D8B'     # 청회색
    }
    
    # 제목
    ax.text(10, 13.5, 'ISPL2 보험약관 AI 시스템 - 현재 구현 아키텍처', 
            fontsize=18, fontweight='bold', ha='center')
    
    # 1. 프론트엔드 레이어 (상단)
    frontend_box = FancyBboxPatch((0.5, 11), 19, 1.8, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor=colors['frontend'], 
                                  alpha=0.3, edgecolor=colors['frontend'])
    ax.add_patch(frontend_box)
    ax.text(10, 12.3, '🖥️ 프론트엔드 레이어 (React + Next.js + TypeScript)', 
            fontsize=14, fontweight='bold', ha='center', color='white')
    
    # 프론트엔드 컴포넌트들
    frontend_components = [
        ('ChatInterface.tsx\n💬 AI 채팅', 1.5, 11.3),
        ('PolicyManagement.tsx\n📋 약관 관리', 4.5, 11.3),
        ('WorkflowMonitoring.tsx\n📊 워크플로우 모니터링', 7.5, 11.3),
        ('PerformanceDashboard.tsx\n📈 성능 대시보드', 11, 11.3),
        ('API Client (api.ts)\n🔌 HTTP 통신', 14.5, 11.3),
        ('AuthContext.tsx\n🔐 인증 관리', 17.5, 11.3)
    ]
    
    for name, x, y in frontend_components:
        comp_box = FancyBboxPatch((x-0.7, y-0.3), 1.4, 0.6, 
                                  boxstyle="round,pad=0.05", 
                                  facecolor=colors['frontend'], 
                                  alpha=0.7)
        ax.add_patch(comp_box)
        ax.text(x, y, name, fontsize=8, ha='center', va='center', color='white', fontweight='bold')
    
    # 2. 백엔드 API 레이어
    backend_box = FancyBboxPatch((0.5, 8.5), 19, 1.8, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=colors['backend'], 
                                 alpha=0.3, edgecolor=colors['backend'])
    ax.add_patch(backend_box)
    ax.text(10, 9.8, '🚀 백엔드 API 레이어 (FastAPI + Python)', 
            fontsize=14, fontweight='bold', ha='center', color='white')
    
    # API 라우터들
    api_routers = [
        ('/auth/*\n🔑 인증 API', 2, 8.8),
        ('/policies/*\n📋 약관 API', 5, 8.8),
        ('/search/*\n🔍 검색 API', 8, 8.8),
        ('/workflow/*\n📈 워크플로우 API', 11, 8.8),
        ('/dashboard/*\n📊 대시보드 API', 14, 8.8),
        ('JWT + SQLAlchemy\n🛠️ 서비스', 17, 8.8)
    ]
    
    for name, x, y in api_routers:
        router_box = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor=colors['backend'], 
                                    alpha=0.7)
        ax.add_patch(router_box)
        ax.text(x, y, name, fontsize=8, ha='center', va='center', color='white', fontweight='bold')
    
    # 3. Multi-Agent 시스템 레이어
    agents_box = FancyBboxPatch((0.5, 5.5), 19, 2.5, 
                                boxstyle="round,pad=0.1", 
                                facecolor=colors['agents'], 
                                alpha=0.3, edgecolor=colors['agents'])
    ax.add_patch(agents_box)
    ax.text(10, 7.6, '🤖 Multi-Agent 시스템 (LangGraph)', 
            fontsize=14, fontweight='bold', ha='center', color='white')
    
    # Supervisor Agent (중앙)
    supervisor_box = FancyBboxPatch((8.5, 6.8), 3, 0.7, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor=colors['agents'], 
                                    alpha=0.9)
    ax.add_patch(supervisor_box)
    ax.text(10, 7.15, 'Supervisor Agent\n🎯 워크플로우 조율', 
            fontsize=10, ha='center', va='center', color='white', fontweight='bold')
    
    # 개별 에이전트들
    agents = [
        ('PDF Processor\n📄 PDF 분석', 2, 6.2),
        ('Text Processor\n📝 텍스트 추출', 4.5, 6.2),
        ('Table Processor\n📊 표 처리', 7, 6.2),
        ('Image Processor\n🖼️ 이미지 OCR', 13, 6.2),
        ('Markdown Processor\n📝 MD 변환', 15.5, 6.2),
        ('Embedding Agent\n🧠 임베딩 생성', 18, 6.2)
    ]
    
    for name, x, y in agents:
        agent_box = FancyBboxPatch((x-0.7, y-0.3), 1.4, 0.6, 
                                   boxstyle="round,pad=0.05", 
                                   facecolor=colors['agents'], 
                                   alpha=0.7)
        ax.add_patch(agent_box)
        ax.text(x, y, name, fontsize=8, ha='center', va='center', color='white', fontweight='bold')
        
        # Supervisor에서 각 에이전트로 화살표
        arrow = ConnectionPatch((10, 6.8), (x, y+0.3), "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5, 
                               mutation_scale=15, fc=colors['agents'], alpha=0.6)
        ax.add_patch(arrow)
    
    # 4. 데이터베이스 레이어
    db_box = FancyBboxPatch((0.5, 3), 9, 1.8, 
                            boxstyle="round,pad=0.1", 
                            facecolor=colors['database'], 
                            alpha=0.3, edgecolor=colors['database'])
    ax.add_patch(db_box)
    ax.text(5, 4.3, '🗄️ 데이터베이스 레이어 (PostgreSQL + pgvector)', 
            fontsize=12, fontweight='bold', ha='center', color='white')
    
    # 데이터베이스 테이블들
    db_tables = [
        ('users\n👥 사용자', 1.5, 3.5),
        ('policies\n📋 약관', 3.5, 3.5),
        ('workflow_logs\n📈 워크플로우', 5.5, 3.5),
        ('embeddings\n🧠 벡터', 7.5, 3.5)
    ]
    
    for name, x, y in db_tables:
        table_box = FancyBboxPatch((x-0.6, y-0.25), 1.2, 0.5, 
                                   boxstyle="round,pad=0.05", 
                                   facecolor=colors['database'], 
                                   alpha=0.7)
        ax.add_patch(table_box)
        ax.text(x, y, name, fontsize=8, ha='center', va='center', color='white', fontweight='bold')
    
    # 5. 외부 서비스 레이어
    external_box = FancyBboxPatch((10.5, 3), 9, 1.8, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor=colors['external'], 
                                  alpha=0.3, edgecolor=colors['external'])
    ax.add_patch(external_box)
    ax.text(15, 4.3, '🌐 외부 서비스 연동', 
            fontsize=12, fontweight='bold', ha='center', color='white')
    
    # 외부 서비스들
    external_services = [
        ('OpenAI API\n🤖 GPT-4', 11.5, 3.5),
        ('LangFuse\n📊 모니터링', 14, 3.5),
        ('MCP Protocol\n🔗 도구 호출', 16.5, 3.5),
        ('pgvector\n🔍 벡터 검색', 18.5, 3.5)
    ]
    
    for name, x, y in external_services:
        service_box = FancyBboxPatch((x-0.6, y-0.25), 1.2, 0.5, 
                                     boxstyle="round,pad=0.05", 
                                     facecolor=colors['external'], 
                                     alpha=0.7)
        ax.add_patch(service_box)
        ax.text(x, y, name, fontsize=8, ha='center', va='center', color='white', fontweight='bold')
    
    # 6. 모니터링 & 성능 레이어
    monitoring_box = FancyBboxPatch((0.5, 0.5), 19, 1.8, 
                                    boxstyle="round,pad=0.1", 
                                    facecolor=colors['monitoring'], 
                                    alpha=0.3, edgecolor=colors['monitoring'])
    ax.add_patch(monitoring_box)
    ax.text(10, 1.8, '📊 모니터링 & 성능 추적', 
            fontsize=12, fontweight='bold', ha='center', color='white')
    
    # 모니터링 컴포넌트들
    monitoring_components = [
        ('Workflow Logger\n📋 로그 수집', 2.5, 1),
        ('Performance Collector\n📈 성능 수집', 6, 1),
        ('Real-time Dashboard\n📊 실시간 대시보드', 10, 1),
        ('LangFuse Integration\n🔗 외부 모니터링', 14, 1),
        ('Alert System\n🚨 알림 시스템', 17.5, 1)
    ]
    
    for name, x, y in monitoring_components:
        mon_box = FancyBboxPatch((x-0.8, y-0.25), 1.6, 0.5, 
                                 boxstyle="round,pad=0.05", 
                                 facecolor=colors['monitoring'], 
                                 alpha=0.7)
        ax.add_patch(mon_box)
        ax.text(x, y, name, fontsize=8, ha='center', va='center', color='white', fontweight='bold')
    
    # 주요 데이터 플로우 화살표들
    # 프론트엔드 -> 백엔드
    main_flow1 = ConnectionPatch((10, 11), (10, 10.3), "data", "data",
                                arrowstyle="->", shrinkA=5, shrinkB=5, 
                                mutation_scale=20, fc='black', linewidth=2)
    ax.add_patch(main_flow1)
    
    # 백엔드 -> Multi-Agent
    main_flow2 = ConnectionPatch((10, 8.5), (10, 8), "data", "data",
                                arrowstyle="->", shrinkA=5, shrinkB=5, 
                                mutation_scale=20, fc='black', linewidth=2)
    ax.add_patch(main_flow2)
    
    # Multi-Agent -> 데이터베이스
    main_flow3 = ConnectionPatch((7, 5.5), (5, 4.8), "data", "data",
                                arrowstyle="->", shrinkA=5, shrinkB=5, 
                                mutation_scale=20, fc='black', linewidth=2)
    ax.add_patch(main_flow3)
    
    # Multi-Agent -> 외부 서비스
    main_flow4 = ConnectionPatch((13, 5.5), (15, 4.8), "data", "data",
                                arrowstyle="->", shrinkA=5, shrinkB=5, 
                                mutation_scale=20, fc='black', linewidth=2)
    ax.add_patch(main_flow4)
    
    # 모니터링 연결
    monitoring_flow = ConnectionPatch((10, 5.5), (10, 2.3), "data", "data",
                                     arrowstyle="->", shrinkA=5, shrinkB=5, 
                                     mutation_scale=15, fc=colors['monitoring'], 
                                     linestyle='--', alpha=0.7)
    ax.add_patch(monitoring_flow)
    
    # 범례
    legend_elements = [
        ('프론트엔드', colors['frontend']),
        ('백엔드 API', colors['backend']),
        ('AI 에이전트', colors['agents']),
        ('데이터베이스', colors['database']),
        ('외부 서비스', colors['external']),
        ('모니터링', colors['monitoring'])
    ]
    
    legend_x = 0.5
    legend_y = 12.5
    ax.text(legend_x, legend_y, '범례:', fontsize=10, fontweight='bold')
    
    for i, (label, color) in enumerate(legend_elements):
        y_pos = legend_y - 0.3 * (i + 1)
        legend_patch = FancyBboxPatch((legend_x, y_pos-0.05), 0.3, 0.1, 
                                      boxstyle="round,pad=0.02", 
                                      facecolor=color, alpha=0.7)
        ax.add_patch(legend_patch)
        ax.text(legend_x + 0.4, y_pos, label, fontsize=8, va='center')
    
    # 주요 특징 표시
    features_text = """
    주요 구현 특징:
    • Multi-Agent LangGraph 워크플로우
    • 실시간 성능 모니터링
    • pgvector 기반 RAG 검색
    • JWT 인증 시스템
    • 워크플로우 로그 추적
    • React 기반 대시보드
    """
    
    ax.text(16, 11, features_text, fontsize=9, va='top', 
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    
    # 이미지 저장
    output_file = "current_ispl2_architecture.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    
    print(f"✅ 현재 구현 아키텍처 다이어그램이 '{output_file}'에 저장되었습니다.")
    
    try:
        plt.show()
    except:
        print("💡 GUI 환경이 아니어서 그래프를 화면에 표시할 수 없습니다.")
        print(f"   저장된 파일을 확인하세요: {output_file}")

def create_data_flow_diagram():
    """데이터 플로우 다이어그램 생성"""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # 제목
    ax.text(8, 11.5, 'ISPL2 데이터 플로우 다이어그램', 
            fontsize=16, fontweight='bold', ha='center')
    
    # 플로우 단계들
    flow_steps = [
        # (텍스트, x, y, 색상)
        ('사용자\n📱', 2, 10, '#2196F3'),
        ('React UI\n🖥️', 2, 8.5, '#2196F3'),
        ('API Client\n🔌', 2, 7, '#2196F3'),
        ('FastAPI\n🚀', 6, 7, '#4CAF50'),
        ('Supervisor\n🎯', 10, 7, '#FF5722'),
        ('PDF 처리\n📄', 8, 5.5, '#FF5722'),
        ('텍스트 추출\n📝', 10, 5.5, '#FF5722'),
        ('임베딩 생성\n🧠', 12, 5.5, '#FF5722'),
        ('Vector DB\n🗄️', 10, 4, '#9C27B0'),
        ('RAG 검색\n🔍', 10, 2.5, '#4CAF50'),
        ('GPT-4 응답\n🤖', 6, 2.5, '#FF9800'),
        ('결과 반환\n📋', 2, 2.5, '#2196F3')
    ]
    
    # 각 단계 그리기
    for text, x, y, color in flow_steps:
        box = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8, 
                            boxstyle="round,pad=0.1", 
                            facecolor=color, alpha=0.7, edgecolor=color)
        ax.add_patch(box)
        ax.text(x, y, text, fontsize=9, ha='center', va='center', 
                color='white', fontweight='bold')
    
    # 플로우 화살표들
    arrows = [
        # (시작x, 시작y, 끝x, 끝y)
        (2, 9.6, 2, 8.9),    # 사용자 -> React UI
        (2, 8.1, 2, 7.4),    # React UI -> API Client
        (2.6, 7, 5.4, 7),    # API Client -> FastAPI
        (6.6, 7, 9.4, 7),    # FastAPI -> Supervisor
        (10, 6.6, 8, 5.9),   # Supervisor -> PDF 처리
        (10, 6.6, 10, 5.9),  # Supervisor -> 텍스트 추출
        (10, 6.6, 12, 5.9),  # Supervisor -> 임베딩 생성
        (10, 5.1, 10, 4.4),  # 텍스트 추출 -> Vector DB
        (10, 3.6, 10, 2.9),  # Vector DB -> RAG 검색
        (9.4, 2.5, 6.6, 2.5), # RAG 검색 -> GPT-4 응답
        (5.4, 2.5, 2.6, 2.5), # GPT-4 응답 -> 결과 반환
        (2, 2.9, 2, 6.6),    # 결과 반환 -> API Client (역방향)
    ]
    
    for start_x, start_y, end_x, end_y in arrows:
        arrow = ConnectionPatch((start_x, start_y), (end_x, end_y), "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5, 
                               mutation_scale=15, fc='black', alpha=0.7)
        ax.add_patch(arrow)
    
    # 모니터링 플로우 (별도 색상)
    monitoring_steps = [
        ('LangFuse\n📊', 14, 9, '#607D8B'),
        ('Workflow Logger\n📋', 14, 7, '#607D8B'),
        ('Performance\n📈', 14, 5, '#607D8B'),
        ('Dashboard\n📊', 14, 3, '#607D8B')
    ]
    
    for text, x, y, color in monitoring_steps:
        box = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8, 
                            boxstyle="round,pad=0.1", 
                            facecolor=color, alpha=0.7, edgecolor=color)
        ax.add_patch(box)
        ax.text(x, y, text, fontsize=9, ha='center', va='center', 
                color='white', fontweight='bold')
    
    # 모니터링 연결선들 (점선)
    monitoring_arrows = [
        (10.6, 7, 13.4, 7),   # Supervisor -> Workflow Logger
        (14, 6.6, 14, 5.4),   # Workflow Logger -> Performance
        (14, 4.6, 14, 3.4),   # Performance -> Dashboard
    ]
    
    for start_x, start_y, end_x, end_y in monitoring_arrows:
        arrow = ConnectionPatch((start_x, start_y), (end_x, end_y), "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5, 
                               mutation_scale=12, fc='#607D8B', alpha=0.6,
                               linestyle='--')
        ax.add_patch(arrow)
    
    plt.tight_layout()
    
    # 이미지 저장
    output_file = "ispl2_data_flow.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    
    print(f"✅ 데이터 플로우 다이어그램이 '{output_file}'에 저장되었습니다.")

if __name__ == "__main__":
    print("🎨 ISPL2 현재 구현 아키텍처 다이어그램 생성 도구")
    print("="*60)
    
    # 1. 전체 시스템 아키텍처
    print("\n1. 전체 시스템 아키텍처 다이어그램 생성 중...")
    create_current_architecture_diagram()
    
    # 2. 데이터 플로우 다이어그램
    print("\n2. 데이터 플로우 다이어그램 생성 중...")
    create_data_flow_diagram()
    
    print("\n✅ 모든 다이어그램 생성 완료!")
    print("생성된 파일:")
    print("  - current_ispl2_architecture.png")
    print("  - ispl2_data_flow.png")




