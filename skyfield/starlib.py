"""Python classes that represent various classes of star."""

from numpy import array, cos, outer, sin
from .constants import AU_KM, ASEC2RAD, C, C_AUDAY, DAY_S, T0
from .functions import length_of
from .positionlib import Astrometric
from .relativity import light_time_difference
from .units import Angle

class Star(object):

    au_km = AU_KM

    def __init__(self, ra=None, dec=None, ra_hours=None, dec_degrees=None,
                 ra_mas_per_year=0.0, dec_mas_per_year=0.0,
                 parallax_mas=0.0, radial_km_per_s=0.0, names=()):

        if ra_hours is not None:
            self.ra = Angle(hours=ra_hours)
        elif isinstance(ra, Angle):
            self.ra = ra
        else:
            raise TypeError('please provide either ra_hours=<float> or else'
                            ' ra=<skyfield.units.Angle object>')

        if dec_degrees is not None:
            self.dec = Angle(degrees=dec_degrees)
        elif isinstance(dec, Angle):
            self.dec = dec
        else:
            raise TypeError('please provide either dec_degrees=<float> or else'
                            ' dec=<skyfield.units.Angle object>')

        self.ra_mas_per_year = ra_mas_per_year
        self.dec_mas_per_year = dec_mas_per_year
        self.parallax_mas = parallax_mas
        self.radial_km_per_s = radial_km_per_s
        self.names = names

        self._compute_vectors()

    def __repr__(self):
        opts = []
        for name in ['ra_mas_per_year', 'dec_mas_per_year',
                     'parallax_mas', 'radial_km_per_s', 'names']:
            value = getattr(self, name)
            if value:
                opts.append(', {0}={1!r}'.format(name, value))
        return 'Star(ra_hours={0!r}, dec_degrees={1!r}{2})'.format(
            self.ra.hours, self.dec.degrees, ''.join(opts))

    def _observe_from_bcrs(self, observer):
        position, velocity = self._position_au, self._velocity_au_per_d
        t = observer.t
        dt = light_time_difference(position, observer.position.au)
        if t.shape:
            position = (outer(velocity, t.tdb + dt - T0).T + position).T
        else:
            position = position + velocity * (t.tdb + dt - T0)
        vector = position - observer.position.au
        distance = length_of(vector)
        light_time = distance / C_AUDAY

        g = Astrometric(vector, (observer.velocity.au_per_d.T - velocity).T, t)
        g.observer = observer
        g.distance = distance
        g.light_time = light_time
        return g

    def _compute_vectors(self):
        """Compute the star's position as an ICRS position and velocity."""

        # Use 1 gigaparsec for stars whose parallax is zero.

        parallax = self.parallax_mas
        if parallax <= 0.0:
            parallax = 1.0e-6

        # Convert right ascension, declination, and parallax to position
        # vector in equatorial system with units of au.

        dist = 1.0 / sin(parallax * 1.0e-3 * ASEC2RAD)
        r = self.ra.radians
        d = self.dec.radians
        cra = cos(r)
        sra = sin(r)
        cdc = cos(d)
        sdc = sin(d)

        self._position_au = array((
            dist * cdc * cra,
            dist * cdc * sra,
            dist * sdc,
            ))

        # Compute Doppler factor, which accounts for change in light
        # travel time to star.

        k = 1.0 / (1.0 - self.radial_km_per_s / C * 1000.0)

        # Convert proper motion and radial velocity to orthogonal
        # components of motion with units of au/day.

        pmr = self.ra_mas_per_year / (parallax * 365.25) * k
        pmd = self.dec_mas_per_year / (parallax * 365.25) * k
        rvl = self.radial_km_per_s * DAY_S / self.au_km * k

        # Transform motion vector to equatorial system.

        self._velocity_au_per_d = array((
            - pmr * sra - pmd * sdc * cra + rvl * cdc * cra,
              pmr * cra - pmd * sdc * sra + rvl * cdc * sra,
              pmd * cdc + rvl * sdc,
              ))
