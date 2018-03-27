class TeamPosition:
    """Represents a team's league weekly league position."""
    def __init__(self,team_name,points=0):
        self.team = team_name
        self.points = points
        self.position = []

    def __str__(self):
        return 'team={0}, points={1}, position={2}'.format(self.team,self.points,self.position)

#sort the list by points
#populate TeamPosition position[] for each instance
