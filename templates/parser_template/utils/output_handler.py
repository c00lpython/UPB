# utils/output_handler.py
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OutputHandler:
    """Сохранение результатов + Plotly графики + привязка к пользователю"""

    RESULTS_DIR = Path(__file__).parent.parent / "results"

    @staticmethod
    def save_results(data: list, project_name: str, user_id: int = None, output_path: str = "./output", formats: list = None) -> dict:
        """Сохраняет данные в указанных форматах с привязкой к пользователю"""
        if not data:
            logger.warning("No data to save")
            return {"success": False, "error": "No data", "records": 0}

        df = pd.DataFrame(data)

        # Папка пользователя
        if user_id:
            results_dir = OutputHandler.RESULTS_DIR / f"user_{user_id}" / (project_name or "default")
        else:
            results_dir = OutputHandler.RESULTS_DIR / (project_name or "default")

        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = output_path.replace('./', '').replace('/', '_')
        base_filename = f"{safe_name}_{timestamp}"

        saved_files = []
        formats = formats or ["excel"]

        # 1. Excel (с метаданными)
        if "excel" in formats:
            filepath = results_dir / f"{base_filename}.xlsx"
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Parsed Data', index=False)
                metadata = pd.DataFrame([
                    ['Project', project_name or 'N/A'],
                    ['Timestamp', timestamp],
                    ['Records', len(data)],
                    ['Columns', ', '.join(df.columns)],
                ], columns=['Property', 'Value'])
                metadata.to_excel(writer, sheet_name='Metadata', index=False)
            saved_files.append(str(filepath))
            logger.info(f"💾 Saved Excel: {filepath}")

        # 2. CSV
        if "csv" in formats:
            filepath = results_dir / f"{base_filename}.csv"
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            saved_files.append(str(filepath))
            logger.info(f"💾 Saved CSV: {filepath}")

        # 3. JSON
        if "json" in formats:
            filepath = results_dir / f"{base_filename}.json"
            df.to_json(filepath, orient='records', force_ascii=False, indent=2)
            saved_files.append(str(filepath))
            logger.info(f"💾 Saved JSON: {filepath}")

        # 4. Plotly график
        if "plotly" in formats:
            plotly_path = OutputHandler.generate_plotly_report(df, results_dir, project_name, timestamp)
            if plotly_path:
                saved_files.append(plotly_path)

        # Сохраняем в БД, если есть user_id
        if user_id:
            from utils.db_handler import UserDB
            for file_path in saved_files:
                file_path_obj = Path(file_path)
                UserDB.add_result(
                    user_id=user_id,
                    project_name=project_name,
                    file_path=file_path,
                    file_name=file_path_obj.name,
                    records=len(data)
                )

        return {
            "success": True,
            "files": saved_files,
            "records": len(data),
            "project": project_name,
            "timestamp": timestamp
        }

    @staticmethod
    def generate_plotly_report(df: pd.DataFrame, results_dir: Path, project_name: str, timestamp: str) -> Optional[str]:
        """Генерирует Plotly HTML-отчёт со статистикой"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            logger.info("📊 No numeric columns for Plotly")
            return None

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Price Distribution", "Records by Variable", "Top Values", "Stats Summary"),
            specs=[[{"type": "histogram"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "table"}]]
        )

        price_col = next((c for c in numeric_cols if 'price' in c.lower() or 'cost' in c.lower()), numeric_cols[0])
        fig.add_trace(
            go.Histogram(x=df[price_col], nbinsx=20, name=price_col, marker_color='#4CAF50'),
            row=1, col=1
        )

        if 'var' in df.columns:
            var_counts = df['var'].value_counts().head(10)
            fig.add_trace(
                go.Bar(x=var_counts.index, y=var_counts.values, name='Records by var', marker_color='#2196F3'),
                row=1, col=2
            )

        top_values = df.nlargest(10, numeric_cols[0])[[numeric_cols[0]]].reset_index(drop=True)
        fig.add_trace(
            go.Bar(
                x=top_values.index,
                y=top_values[numeric_cols[0]],
                name='Top 10',
                marker_color='#FF9800',
                text=top_values[numeric_cols[0]],
                textposition='outside'
            ),
            row=2, col=1
        )

        stats = []
        for col in numeric_cols[:5]:
            stats.append([col, df[col].min(), df[col].max(), df[col].mean(), df[col].median()])

        fig.add_trace(
            go.Table(
                header=dict(values=['Column', 'Min', 'Max', 'Mean', 'Median'],
                            fill_color='#4CAF50', align='left',
                            font=dict(color='white', size=12)),
                cells=dict(values=list(zip(*stats)),
                           fill_color='#f9f9f9', align='left',
                           font=dict(size=11))
            ),
            row=2, col=2
        )

        fig.update_layout(
            height=800,
            title_text=f"📊 Parser Report: {project_name}",
            showlegend=False,
            template='plotly_white'
        )

        filepath = results_dir / f"report_{timestamp}.html"
        fig.write_html(str(filepath))
        logger.info(f"📊 Plotly report saved: {filepath}")
        return str(filepath)

    @staticmethod
    def get_user_projects(user_id: int) -> List[str]:
        """Возвращает список проектов пользователя"""
        from utils.db_handler import UserDB
        results = UserDB.get_user_results(user_id)
        projects = set()
        for r in results:
            projects.add(r["project_name"])
        return sorted(list(projects))

    @staticmethod
    def get_user_files(user_id: int, project_name: str) -> List[Dict[str, Any]]:
        """Возвращает файлы пользователя по проекту"""
        from utils.db_handler import UserDB
        results = UserDB.get_user_results(user_id)
        files = []
        for r in results:
            if r["project_name"] == project_name:
                file_path = Path(r["file_path"])
                files.append({
                    "id": r["id"],
                    "name": r["file_name"],
                    "path": r["file_path"],
                    "records": r["records"],
                    "size": file_path.stat().st_size if file_path.exists() else 0,
                    "modified": file_path.stat().st_mtime if file_path.exists() else 0,
                })
        return sorted(files, key=lambda x: x["modified"], reverse=True)

    @staticmethod
    def get_latest_excel(user_id: int, project_name: str) -> Optional[Path]:
        """Возвращает путь к последнему Excel-файлу пользователя"""
        from utils.db_handler import UserDB
        results = UserDB.get_user_results(user_id)
        excel_files = []
        for r in results:
            if r["project_name"] == project_name and r["file_path"].endswith('.xlsx'):
                excel_files.append(Path(r["file_path"]))
        if not excel_files:
            return None
        return max(excel_files, key=lambda f: f.stat().st_mtime if f.exists() else 0)