/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

/**
 * @author olegus
 *
 */
public interface Call {
	Callable getCallable();
	List<ActualArgument> getArguments();
}
