import json
from datetime import timedelta
from django.core.management.base import BaseCommand
from core.handlers.analysis import get_chart_data_json
import matplotlib.pyplot as plt  # Import Matplotlib
from io import BytesIO
import base64
# ... (your other imports and the analysis/chart functions)

class Command(BaseCommand):
    help = 'Generates chart data from request logs and saves it to a PNG image file.'

    def handle(self, *args, **options):
        chart_json = get_chart_data_json()
        chart_data = json.loads(chart_json)

        # Create the Matplotlib chart
        labels = chart_data['labels']
        success_data = chart_data['datasets'][0]['data']  # Assuming the first dataset is success
        failure_data = chart_data['datasets'][1]['data']  # And the second is failure

        x = range(len(labels))  # the label locations

        width = 0.35  # the width of the bars

        fig, ax = plt.subplots()
        rects1 = ax.bar(x, success_data, width, label='Success')
        rects2 = ax.bar([i + width for i in x], failure_data, width, label='Failure')

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Counts')
        ax.set_title('Request Log Analysis')
        ax.set_xticks([i + width / 2 for i in x])
        ax.set_xticklabels(labels)
        ax.legend()


        def autolabel(rects):
            """Attach a text label above each bar in *rects*, displaying its height."""
            for rect in rects:
                height = rect.get_height()
                ax.annotate('{}'.format(height),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')


        autolabel(rects1)
        autolabel(rects2)

        fig.tight_layout()

        # Save the chart to a PNG image file
        plt.savefig('chart.png')

        self.stdout.write(self.style.SUCCESS('Chart image (chart.png) generated.'))