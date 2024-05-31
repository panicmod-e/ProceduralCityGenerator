# The streamlineParameters class holds the parameters to control streamline generation.
#
# dsep: separation distance between streamline seeds
# dtest: streamline integration separating distance
# dstep: step size during streamline integration
# dcirclejoin: distance to look for circle joining
# dlookahead: distance to look ahead for joining dangling streamlines
# djoinangle: angle (radians) at which to join roads
# path_iterations: upper limit for path integration
# seed_tries: upper limit for attempts to sample random seed
# simplify_tolerance: tolerance for polyline simplification (see Douglas-Peucker)
# collide_early: change of early collision, 0-1
class StreamlineParameters:
    def __init__(
            self,
            dsep,
            dtest,
            dstep,
            dcirclejoin,
            dlookahead,
            joinangle,
            path_iterations,
            seed_tries,
            simplify_tolerance,
            collide_early):
        self.dsep = dsep
        self.dtest = dtest
        self.dstep = dstep
        self.dcirclejoin = dcirclejoin
        self.dlookahead = dlookahead
        self.joinangle = joinangle
        self.path_iterations = path_iterations
        self.seed_tries = seed_tries
        self.simplify_tolerance = simplify_tolerance
        self.collide_early = collide_early

    def copy(self):
        return StreamlineParameters(
            self.dsep,
            self.dtest,
            self.dstep,
            self.dcirclejoin,
            self.dlookahead,
            self.joinangle,
            self.path_iterations,
            self.seed_tries,
            self.simplify_tolerance,
            self.collide_early
        )

    def copy_sq(self):
        return StreamlineParameters(
            self.dsep ** 2,
            self.dtest ** 2,
            self.dstep ** 2,
            self.dcirclejoin ** 2,
            self.dlookahead ** 2,
            self.joinangle ** 2,
            self.path_iterations ** 2,
            self.seed_tries ** 2,
            self.simplify_tolerance ** 2,
            self.collide_early ** 2
        )
