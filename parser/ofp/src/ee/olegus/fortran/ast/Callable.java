/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.Collection;
import java.util.List;

/**
 * @author olegus
 *
 */
public interface Callable {
	String getName();
	
	/**
	 * @return collection of allowed arguments (1 in case of usual subroutine, 
	 *  more than 0 in case of interface)
	 */
	Collection<List<? extends TypeShape>> getArgumentLists();
}
