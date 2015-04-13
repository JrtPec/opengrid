class Analysis(object):
    """
        Abstract class for all Open Grid Analyses.

        Every analysis should output results as JSON and plot.
    """

    def __init__(self,analysis_id=None):
        self.analysis_id = analysis_id
        
    def to_json(self):
        raise NotImplementedError("Subclass must implement abstract method")
        
    def to_plt(self):
        raise NotImplementedError("Subclass must implement abstract method")