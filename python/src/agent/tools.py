"""LangChain tools for document processing."""

import os
import json
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


class DocumentTools:
    """Tools for reading Word/Excel documents and generating charts."""

    @staticmethod
    @tool
    def read_excel_file(file_path: str) -> str:
        """Read an Excel file and return its contents as markdown tables.

        Args:
            file_path: Path to the Excel file (.xlsx, .xls)

        Returns:
            Markdown representation of all sheets and data
        """
        import pandas as pd
        print("****read_excel_file*****")
        try:
            xl = pd.ExcelFile(file_path)
            result = []
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                result.append(f"### Sheet: {sheet_name}\n")
                result.append(df.to_markdown(index=False))
            return "\n\n".join(result)
        except Exception as e:
            print(f"****read_excel_file  error: *****{e}")
            return f"Error reading Excel file: {str(e)}"

    @staticmethod
    @tool
    def read_word_file(file_path: str) -> str:
        """Read a Word document and return its text content for analysis.

        Args:
            file_path: Path to the Word file (.docx, .doc)

        Returns:
            Text content of the document
        """
        from langchain_community.document_loaders import Docx2txtLoader

        try:
            loader = Docx2txtLoader(file_path)
            docs = loader.load()
            return "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            return f"Error reading Word file: {str(e)}"

    @staticmethod
    @tool
    def generate_chart(image_id: str, chart_type: str, data: str, options: str = "{}") -> str:
        """Generate a chart image and save to file, return URL for display.

        Args:
            image_id: Unique identifier for naming the output image
            chart_type: Type of chart - "heatmap", "bar", "line", "pie", "scatter", "histogram"
            data: JSON string with data in format:
                  {"x": [...], "y": [...]} for line/bar/scatter
                  {"values": [...]} for pie/histogram
                  {"matrix": [[...], [...]], "x_labels": [...], "y_labels": [...]} for heatmap
            options: JSON string with optional styling:
                     {"title": "Chart Title", "xlabel": "X Axis", "ylabel": "Y Axis", "width": 800, "height": 600}

        Returns:
            URL path to the saved chart image for display in browser
        """
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')

        try:
            parsed_data = json.loads(data)
            parsed_options = json.loads(options) if options else {}

            title = parsed_options.get("title", "")
            xlabel = parsed_options.get("xlabel", "")
            ylabel = parsed_options.get("ylabel", "")
            width = parsed_options.get("width", 800)
            height = parsed_options.get("height", 500)

            fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)

            if chart_type == "heatmap":
                matrix = parsed_data.get("matrix", [])
                x_labels = parsed_data.get("x_labels", [str(i) for i in range(len(matrix[0]) if matrix else 0)])
                y_labels = parsed_data.get("y_labels", [str(i) for i in range(len(matrix))])
                im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
                ax.set_xticks(range(len(x_labels)))
                ax.set_yticks(range(len(y_labels)))
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
                ax.set_yticklabels(y_labels)
                plt.colorbar(im, ax=ax)
                if title:
                    ax.set_title(title)
                if xlabel:
                    ax.set_xlabel(xlabel)
                if ylabel:
                    ax.set_ylabel(ylabel)

            elif chart_type == "bar":
                x = parsed_data.get("x", [])
                y = parsed_data.get("y", [])
                ax.bar(x, y, color='steelblue')
                if title:
                    ax.set_title(title)
                if xlabel:
                    ax.set_xlabel(xlabel)
                if ylabel:
                    ax.set_ylabel(ylabel)
                ax.tick_params(axis='x', rotation=45)

            elif chart_type == "line":
                x = parsed_data.get("x", [])
                y = parsed_data.get("y", [])
                ax.plot(x, y, marker='o', color='steelblue', linewidth=2)
                if title:
                    ax.set_title(title)
                if xlabel:
                    ax.set_xlabel(xlabel)
                if ylabel:
                    ax.set_ylabel(ylabel)

            elif chart_type == "pie":
                values = parsed_data.get("values", [])
                labels = parsed_data.get("labels", [str(i) for i in range(len(values))])
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                if title:
                    ax.set_title(title)

            elif chart_type == "scatter":
                x = parsed_data.get("x", [])
                y = parsed_data.get("y", [])
                ax.scatter(x, y, c='steelblue', alpha=0.6)
                if title:
                    ax.set_title(title)
                if xlabel:
                    ax.set_xlabel(xlabel)
                if ylabel:
                    ax.set_ylabel(ylabel)

            elif chart_type == "histogram":
                values = parsed_data.get("values", [])
                ax.hist(values, bins=20, color='steelblue', edgecolor='white')
                if title:
                    ax.set_title(title)
                if xlabel:
                    ax.set_xlabel(xlabel)
                if ylabel:
                    ax.set_ylabel(ylabel)

            plt.tight_layout()

            # Save to file instead of returning base64
            filename = f"{image_id}_chart.png"
            output_path = OUTPUT_DIR / filename
            print(f"[generate_chart] Saving to: {output_path}")
            plt.savefig(output_path, format='png', dpi=100, bbox_inches='tight',
                      facecolor='white', edgecolor='none')
            plt.close(fig)

            # Return URL path for the image
            result = f"/api/agent/chart/{image_id}"
            print(f"[generate_chart] Returning: {result}")
            return result

        except Exception as e:
            return f"Error generating chart: {str(e)}"


def get_document_tools():
    """Get all document processing tools for the agent."""
    return [
        DocumentTools.read_excel_file,
        DocumentTools.read_word_file,
        DocumentTools.generate_chart,
    ]