/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

/**
 * @author olegus
 *
 */
public interface Scope {
	String getFilename();
	
	TypeShape getVariableOrFunction(String name, List<? extends TypeShape> arguments, boolean immediateScope);
	/**
	 * @param name of the subroutine or function
	 * @param arguments list of arguments for the function or null if does not matter
	 * @param immediateScope limit subroutines only to this scope
	 * @return
	 */
	Subprogram getSubroutine(String name, List<? extends TypeShape> arguments, boolean immediateScope);
	ProgramUnit getModule(String name);
	Type getType(String name);
}
