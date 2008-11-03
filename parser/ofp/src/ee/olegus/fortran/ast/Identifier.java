/**
 * 
 */
package ee.olegus.fortran.ast;

import ee.olegus.fortran.ast.text.Locatable;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class Identifier implements Locatable {
	
	private Location location;
	private String name;
	
	public Identifier(String name) {
		this.name = name;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.text.Locatable#getLocation()
	 */
	public Location getLocation() {
		if(location==null)
			location = new Location();
		return location;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}
}
