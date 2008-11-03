/**
 * 
 */
package ee.olegus.fortran.ast.cpr;

import org.antlr.runtime.CommonToken;

import ee.olegus.fortran.ast.text.Locatable;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class PotentialCheckpoint implements Locatable {
	private Location location;
	private CommonToken token;

	public PotentialCheckpoint(CommonToken token) {
		location = new Location(token.getTokenIndex(), token.getTokenIndex()+1, null, null);
		this.token = token;
	}

	public CommonToken getToken() {
		return token;
	}

	public Location getLocation() {
		return location;
	}

	@Override
	public String toString() {
		return token.toString()+" code:"+location.code;
	}
}
