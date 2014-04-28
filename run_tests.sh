#!/bin/sh

# A good place to look for nose info: http://somethingaboutorange.com/mrl/projects/nose/
rm -f run_functional_tests.log 

show_help() {
cat <<EOF
'${0##*/}'                          for testing all the tools in functional directory
'${0##*/} aaa'                      for testing one test case of 'aaa' ('aaa' is the file name with path)
'${0##*/} -id bbb'                  for testing one tool with id 'bbb' ('bbb' is the tool id)
'${0##*/} -sid ccc'                 for testing one section with sid 'ccc' ('ccc' is the string after 'section::')
'${0##*/} -list'                    for listing all the tool ids
'${0##*/} -toolshed'                for running all the test scripts in the ./test/tool_shed/functional directory
'${0##*/} -toolshed testscriptname' for running one test script named testscriptname in the .test/tool_shed/functional directory
'${0##*/} -workflow test.xml'       for running a workflow test case as defined by supplied workflow xml test file (experimental)
'${0##*/} -framework'               for running through example tool tests testing framework features in test/functional/tools"   
'${0##*/} -framework -id toolid'    for testing one framework tool (in test/functional/tools/) with id 'toolid'
'${0##*/} -data_managers -id data_manager_id'    for testing one Data Manager with id 'data_manager_id'
EOF
}

show_list() {
    python tool_list.py
    echo "==========================================================================================================================================="
    echo "'${0##*/} -id bbb'               for testing one tool with id 'bbb' ('bbb' is the tool id)"
    echo "'${0##*/} -sid ccc'              for testing one section with sid 'ccc' ('ccc' is the string after 'section::')"
}

test_script="./scripts/functional_tests.py"
report_file="run_functional_tests.html"

while :
do
    case "$1" in
      -h|--help|-\?) 
          show_help
          exit 0
          ;;
      -l|-list|--list)
          show_list
          exit 0
          ;;
      -id|--id)
          if [ $# -gt 1 ]; then
              test_id=$2;
              shift 2
          else 
              echo "--id requires an argument" 1>&2
              exit 1
          fi 
          ;;
      -s|-sid|--sid)
          if [ $# -gt 1 ]; then
              section_id=$2
              shift 2
          else 
              echo "--sid requires an argument" 1>&2
              exit 1
          fi 
          ;;
      -t|-toolshed|--toolshed)
          test_script="./test/tool_shed/functional_tests.py"
          report_file="./test/tool_shed/run_functional_tests.html"
          if [ $# -gt 1 ]; then
              toolshed_script=$2
              shift 2
          else
              toolshed_script="./test/tool_shed/functional"
              shift 1
          fi
          ;;
      -w|-workflow|--workflow)
          if [ $# -gt 1 ]; then
              workflow_file=$2
              workflow_test=1
              shift 2
          else 
              echo "--workflow requires an argument" 1>&2
              exit 1
          fi
          ;;
      -f|-framework|--framework)
          framework_test=1;
          shift 1
          ;;
      -d|-data_managers|--data_managers)
          data_managers_test=1;
          shift 1
          ;;
      -m|-migrated|--migrated)
          migrated_test=1;
          shift
          ;;
      -i|-installed|--installed)
          installed_test=1;
          shift
          ;;
      -r|--report_file)
          if [ $# -gt 1 ]; then
              report_file=$2
              shift 2
          else 
              echo "--report_file requires an argument" 1>&2
              exit 1
          fi
          ;;
      --) 
          shift
          break
          ;;
      -*) 
          echo "invalid option: $1" 1>&2;
          show_help
          exit 1
          ;;
      *)
          break;
          ;;
    esac
done

if [ -n "$migrated_test" ] ; then
    [ -n "$test_id" ] && class=":TestForTool_$test_id" || class=""
    extra_args="functional.test_toolbox$class -migrated"
elif [ -n "$installed_test" ] ; then
    [ -n "$test_id" ] && class=":TestForTool_$test_id" || class=""
    extra_args="functional.test_toolbox$class -installed"
elif [ -n "$framework_test" ] ; then
    [ -n "$test_id" ] && class=":TestForTool_$test_id" || class=""
    extra_args="functional.test_toolbox$class -framework"
elif [ -n "$data_managers_test" ] ; then
    [ -n "$test_id" ] && class=":TestForDataManagerTool_$test_id" || class=""
    extra_args="functional.test_data_managers$class -data_managers"
elif [ -n "$workflow_test" ]; then
    extra_args="functional.workflow:WorkflowTestCase $workflow_file"
elif [ -n "$toolshed_script" ]; then
    extra_args="$toolshed_script"
elif [ -n "$section_id" ]; then
    extra_args=`python tool_list.py $section_id` 
elif [ -n "$test_id" ]; then
    class=":TestForTool_$test_id"
    extra_args="functional.test_toolbox$class"
elif [ -n "$1" ] ; then
    extra_args="$1"
else
    extra_args='--exclude="^get" functional'
fi

python $test_script $coverage_arg -v --with-nosehtml --html-report-file $report_file $extra_args
