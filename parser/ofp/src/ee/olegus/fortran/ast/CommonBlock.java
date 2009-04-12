/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

/**
 * @author olegus
 *
 */
public class CommonBlock {

	/**
	 * Block name.
	 */
	private String name;
	/**
	 * List of variable identifiers in block.
	 */
	private List<Entity> entities;

	/**
	 * Get the <code>Name</code> value.
	 *
	 * @return a <code>String</code> value
	 */
	public final String getName() {
		return name;
	}

	/**
	 * Set the <code>Name</code> value.
	 *
	 * @param newName The new Name value.
	 */
	public final void setName(final String newName) {
		this.name = newName;
	}

	public final List<Entity> getEntities() {
		return entities;
	}

	public final void setEntities(final List<Entity> newEntities) {
		this.entities = newEntities;
	}
}
