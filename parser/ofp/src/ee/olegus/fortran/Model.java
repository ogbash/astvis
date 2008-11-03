/**
 * 
 */
package ee.olegus.fortran;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import ee.olegus.fortran.ast.ProgramUnit;
import ee.olegus.fortran.ast.Scope;
import ee.olegus.fortran.ast.Subprogram;
import ee.olegus.fortran.ast.Type;
import ee.olegus.fortran.ast.TypeShape;
import ee.olegus.fortran.model.Module;

/**
 * This object collects some general information about modules, global subroutines and their
 * members.
 * 
 * @author olegus
 *
 */
public class Model implements Scope {
	
	/** modules */
	private Map<String, Module> modules = new HashMap<String, Module>();
	/** global functions and subroutines */
	private Map<String, Subprogram> subpograms = new HashMap<String, Subprogram>();
	
	/** Module list, first members do not depend on later ones.*/
	private List<String> moduleSequence;

	public Map<String, Module> getModules() {
		return modules;
	}

	public void setModules(Map<String, Module> modules) {
		this.modules = modules;
	}

	public List<String> getModuleSequence() {
		return moduleSequence;
	}

	public void setModuleSequence(List<String> moduleSequence) {
		this.moduleSequence = moduleSequence;
	}

	public String getFilename() {
		return null;
	}

	public ProgramUnit getModule(String name) {
		if (modules.containsKey(name.toLowerCase()))
			return modules.get(name.toLowerCase()).getProgramUnit();
		else
			return null;
	}

	public Subprogram getSubroutine(String name, List<? extends TypeShape> arguments, boolean immediateScope) {
		return subpograms.get(name.toLowerCase());
	}

	public Type getType(String name) {
		// TODO Auto-generated method stub
		return null;
	}

	public TypeShape getVariableOrFunction(String name, List<? extends TypeShape> arguments, boolean immediateScope) {
		return subpograms.get(name.toLowerCase());
	}

	public Map<String, Subprogram> getSubpograms() {
		return subpograms;
	}
	
	
}
