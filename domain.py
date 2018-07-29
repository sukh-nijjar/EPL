class TeamPosition:
    """Represents a team's weekly position in the league"""
    def __init__(self,team_name,points=0,scored=0,conceded=0):
        self.team = team_name
        self.points = points
        self.position = []
        self.scored = scored
        self.conceded = conceded

    def goal_difference(self):
        """returns the goals difference for the team"""
        return self.scored - self.conceded

    def __str__(self):
        return 'team={0}, points={1}, position={2}, GD={3}, scored={4}, conceded={5}'.format(self.team,self.points,self.position,self.goal_difference(),self.scored,self.conceded)
