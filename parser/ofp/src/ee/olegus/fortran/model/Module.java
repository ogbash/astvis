/**
 * 
 */
package ee.olegus.fortran.model;

import java.util.HashMap;
import java.util.Map;

import ee.olegus.fortran.ast.ProgramUnit;
import ee.olegus.fortran.ast.Subprogram;

/**
 * @author olegus
 *
 */
public class Module {
	private ProgramUnit programUnit;
	private Map<String,Subprogram> publicSubprograms = new HashMap<String, Subprogram>(4);

	public Module(ProgramUnit unit) {
		this.programUnit = unit;
	}

	public ProgramUnit getProgramUnit() {
		return programUnit;
	}

	public void setProgramUnit(ProgramUnit programUnit) {
		this.programUnit = programUnit;
	}
}
