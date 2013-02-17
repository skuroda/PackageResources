"""
MIT License
Copyright (c) 2013 Scott Kuroda <scott.kuroda@gmail.com>
"""
import sublime
import os
import zipfile
import tempfile
import re
import codecs

def get_package_asset(package_name, asset_name, get_path=False, recursive_search=False, return_binary=False, encoding="utf-8"):
    """
    Retrieve the asset specified in the specified package or None if it
    cannot be found.

    Arguments:
    package_name    Name of the packages whose asset you are searching for.
    asset_name      Name of the asset to search for

    Keyword arguments:
    get_path            Boolean representing if the path or the content of the
                        asset should be returned (default False)

    recursive_search    Boolean representing if the file specified should
                        search for assets recursively or take the file as
                        an absolute path (default False).

    return_binary       Boolean representing if the binary representation of
                        a file should be returned. Only takes affect if get_path
                        is True (default False).

    encoding            String representing the encoding to use when reading.
                        Only takes affect when return_binary is False
                        (default utf-8).

    Return Value:
    None if the asset does not exists. The contents of the asset if get_path is
    False. A path to the file if get_path is True.
    """

    packages_path = sublime.packages_path()
    sublime_package = package_name + ".sublime-package"
    path = None

    if os.path.exists(os.path.join(packages_path, package_name)):
        if recursive_search:
            path = _find_file(os.path.join(packages_path, package_name), asset_name)
        elif os.path.exists(os.path.join(packages_path, package_name, asset_name)):
            path = os.path.join(packages_path, package_name, asset_name)

        if path != None and os.path.exists(path):

            if get_path:
                return  path
            else:
                if return_binary:
                    mode = "rb"
                    encoding = None
                else:
                    mode = "r"
                with codecs.open(path, mode, encoding=encoding) as file_obj:
                    content = file_obj.read()

                return content

    packages_path = sublime.installed_packages_path()

    if os.path.exists(os.path.join(packages_path, sublime_package)):
        ret_value = _search_zip(packages_path, sublime_package, asset_name, get_path, recursive_search, return_binary, encoding)
        if ret_value != None:
            return ret_value

    packages_path = os.path.dirname(sublime.executable_path()) + os.sep + "Packages"

    if os.path.exists(os.path.join(packages_path, sublime_package)):
        ret_value = _search_zip(packages_path, sublime_package, asset_name, get_path, recursive_search, return_binary, encoding)
        if ret_value != None:
            return ret_value
    return None

def get_package_and_asset_name(path):
    """
    This method will return the package name and asset name from a path.

    Arguments:
    path    Path to parse for package and asset name.
    """
    package = None
    asset = None

    if os.path.isabs(path):
        packages_path = sublime.packages_path()
        if path.startswith(packages_path):
            package, asset = _search_for_package_and_asset(path, packages_path)

        packages_path = sublime.installed_packages_path()
        if path.startswith(packages_path):
            package, asset = _search_for_package_and_asset(path, packages_path)

        packages_path = os.path.dirname(sublime.executable_path()) + os.sep + "Packages"
        if path.startswith(packages_path):
            package, asset = _search_for_package_and_asset(path, packages_path)
    else:
        path = re.sub(r"^Packages[/\\]", "", path)
        split = re.split(r"[/\\]", path, 1)
        package = split[0]
        asset = split[1]

    return (package, asset)

def _search_for_package_and_asset(path, packages_path):
    """
    Derive the package and asset from  a path.
    """
    package = os.path.basename(os.path.dirname(path))

    directory, asset = os.path.split(path)
    if directory == packages_path:
        package = asset.replace(".sublime-package", "")
        asset = None
    else:
        package, temp_asset = _search_for_package_and_asset(directory, packages_path)

        if temp_asset is not None:
            temp_asset += os.sep + asset
            asset = temp_asset

    return (package, asset)

def _search_zip(packages_path, package, file_name, path, recursive_search, return_binary, encoding):
    """
    Search a zip for an asset.
    """
    if not os.path.exists(os.path.join(packages_path, package)):
        return None

    ret_value = None
    with zipfile.ZipFile(os.path.join(packages_path, package)) as zip_file:
        namelist = zip_file.namelist()
        if recursive_search:
            indices = [i for i, name in enumerate(namelist) if name.endswith(file_name)]
            if len(indices) > 0:
                file_name = namelist[indices[0]]
        if file_name in namelist:
            if path:
                temp_dir = tempfile.mkdtemp()
                file_location = zip_file.extract(file_name, temp_dir)
                ret_value =  file_location
            else:
                ret_value = zip_file.read(file_name)
                if not return_binary:
                    ret_value = ret_value.decode(encoding)

    return ret_value

def _find_file(abs_dir, file_name):
    """
    Find the absolute path to a specified file. Note that the first entry
    matching the file will be used, even if it exists elsewhere in the
    directory structure.
    """
    ret_path = None

    split = os.path.split(file_name)
    abs_dir = os.path.join(abs_dir, split[0])
    file_name = split[1]

    for root, dirnames, filenames in os.walk(abs_dir):
        if file_name in filenames:
            ret_path = os.path.join(root, file_name)
            break

    return ret_path

##################################### TESTS ####################################
import sys
import unittest

class GetPackageAssetTests(unittest.TestCase):
    def test_get_package_asset(self):
        tc = get_package_asset
        aseq = self.assertEquals

        # Search sublime-package
        res = tc("User", "package_test_asset.txt")
        aseq(res, "")
        res = tc("User", "not_here.txt")
        aseq(res, None)

        # Search user directory

        # abc.txt is a nested resource
        res = tc("User", "abc.txt", True, True)
        aseq(res, os.path.join(sublime.packages_path(), "User", "nested_test", "abc.txt"))
        res = tc("User", "abc.txt", False, True, True)
        aseq(res, b"\xce\xb2")
        res = tc("User", "abc.txt", False, True)
        aseq(res, "β")
        res = tc("User", "abc.txt", False, False)
        aseq(res, None)

        # Specify absolute path
        res = tc("User", "nested_test" + os.sep + "abc.txt", False, True, True)
        aseq(res, b"\xce\xb2")
        res = tc("User", "nested_test" + os.sep + "abc.txt", False, False, True)
        aseq(res, b"\xce\xb2")

    def test_get_package_and_asset_name(self):
        tc = get_package_and_asset_name
        aseq = self.assertEquals

        # Test relative unneted
        r1 = (tc("Packages/Relative/one.py"))
        r2 = (tc("Packages\\Relative\\one.py"))
        r3 = (tc("Packages/Relative/nested/one.py"))
        r4 = (tc("Packages\\Relative\\nested\\one.py"))

        # Test nested
        r5 = (tc("C:\\Abs\\Packages\\ZipPseudo.sublime-package\\nested\\sort.py"))
        r6 = (tc(sublime.packages_path() + "/Absolute/Nested/asset.pth"))
        r7 = (tc(sublime.packages_path() + "\\Absolute\\Nested\\asset.pth"))
        r8 = (tc(sublime.installed_packages_path() + "/Absolute.sublime-package/Nested/asset.pth"))
        r9 = (tc(sublime.installed_packages_path() + "\\Absolute.sublime-package\\Nested\\asset.pth"))
        executable_path = os.path.dirname(sublime.executable_path()) + os.sep + "Packages"
        r10 = (tc(executable_path + "/Absolute.sublime-package/Nested/asset.pth"))
        r11 = (tc(executable_path + "\\Absolute.sublime-package\\Nested\\asset.pth"))

        # Test Unnested
        r12 = (tc(sublime.packages_path() + "/Absolute/asset.pth"))
        r13 = (tc(sublime.packages_path() + "\\Absolute\\asset.pth"))
        r14 = (tc(sublime.installed_packages_path() + "/Absolute.sublime-package/asset.pth"))
        r15 = (tc(sublime.installed_packages_path() + "\\Absolute.sublime-package\\asset.pth"))
        executable_path = os.path.dirname(sublime.executable_path()) + os.sep + "Packages"
        r16 = (tc(executable_path + "/Absolute.sublime-package/asset.pth"))
        r17 = (tc(executable_path + "\\Absolute.sublime-package\\asset.pth"))

        aseq(r1, ('Relative',   'one.py'))
        aseq(r2, ('Relative',   'one.py'))
        aseq(r3, ('Relative',   'nested/one.py'))
        aseq(r4, ('Relative',   'nested\\one.py'))
        aseq(r5, (None,  None))
        aseq(r6, ('Absolute',   'Nested' + os.sep + 'asset.pth'))
        aseq(r7, ('Absolute',   'Nested' + os.sep + 'asset.pth'))
        aseq(r8, ('Absolute',   'Nested' + os.sep + 'asset.pth'))
        aseq(r9, ('Absolute',   'Nested' + os.sep + 'asset.pth'))
        aseq(r10, ('Absolute',   'Nested' + os.sep + 'asset.pth'))
        aseq(r11, ('Absolute',   'Nested' + os.sep + 'asset.pth'))

        aseq(r12, ('Absolute', 'asset.pth'))
        aseq(r13, ('Absolute', 'asset.pth'))
        aseq(r14, ('Absolute', 'asset.pth'))
        aseq(r15, ('Absolute', 'asset.pth'))
        aseq(r16, ('Absolute', 'asset.pth'))
        aseq(r17, ('Absolute', 'asset.pth'))

################ ONLY LOAD TESTS WHEN DEVELOPING NOT ON START UP ###############

try:               times_module_has_been_reloaded  += 1
except NameError:  times_module_has_been_reloaded  =  0       #<em>re</em>loaded

if times_module_has_been_reloaded:
    target = __name__
    suite = unittest.TestLoader().loadTestsFromName(target)

    unittest.TextTestRunner(stream = sys.stdout,  verbosity=0).run(suite)

    print ("running tests", target)
    print ('\nReloads: %s' % times_module_has_been_reloaded)

################################################################################