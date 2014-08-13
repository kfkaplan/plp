import os
import numpy as np

#from libs.process_flat import FlatOff, FlatOn


from libs.path_info import IGRINSPath, IGRINSLog, IGRINSFiles
#import astropy.io.fits as pyfits

from libs.products import PipelineProducts
from libs.apertures import Apertures

#from libs.products import PipelineProducts

if __name__ == "__main__":

    from libs.recipes import load_recipe_list, make_recipe_dict
    from libs.products import PipelineProducts, ProductPath, ProductDB

    if 0:
        utdate = "20140316"
        # log_today = dict(flat_off=range(2, 4),
        #                  flat_on=range(4, 7),
        #                  thar=range(1, 2))
    elif 1:
        utdate = "20140525"
        # log_today = dict(flat_off=range(64, 74),
        #                  flat_on=range(74, 84),
        #                  thar=range(3, 8),
        #                  sky=[29])

    band = "H"
    igr_path = IGRINSPath(utdate)

    igrins_files = IGRINSFiles(igr_path)

    fn = "%s.recipes" % utdate
    recipe_list = load_recipe_list(fn)
    recipe_dict = make_recipe_dict(recipe_list)


if 1:

    obsids = recipe_dict["SKY"][0][0]

    sky_filenames = igrins_files.get_filenames(band, obsids)

    sky_path = ProductPath(igr_path, sky_filenames[0])
    sky_master_obsid = obsids[0]

    # obj_filenames = igrins_files.get_filenames(band, obsids)
    # obj_path = ProductPath(igr_path, obj_filenames[0])
    # obj_master_obsid = obsids[0]

    flatoff_db = ProductDB(os.path.join(igr_path.secondary_calib_path,
                                        "flat_off.db"))
    flaton_db = ProductDB(os.path.join(igr_path.secondary_calib_path,
                                       "flat_on.db"))
    thar_db = ProductDB(os.path.join(igr_path.secondary_calib_path,
                                       "thar.db"))
    # sky_db = ProductDB(os.path.join(igr_path.secondary_calib_path,
    #                                 "sky.db"))

    # basename = sky_db.query(band, obj_master_obsid)
    # sky_path = ProductPath(igr_path, basename)
    raw_spec_products = PipelineProducts.load(sky_path.get_secondary_path("raw_spec"))



    basename = flaton_db.query(band, sky_master_obsid)
    flaton_path = ProductPath(igr_path, basename)

    aperture_solution_products = PipelineProducts.load(flaton_path.get_secondary_path("aperture_solutions"))

    bottomup_solutions = aperture_solution_products["bottom_up_solutions"]


    basename = thar_db.query(band, sky_master_obsid)
    thar_path = ProductPath(igr_path, basename)
    fn = thar_path.get_secondary_path("median_spectra")
    thar_products = PipelineProducts.load(fn)

    # basename = sky_db.query(band, sky_master_obsid)
    # sky_path = ProductPath(igr_path, basename)
    fn = sky_path.get_secondary_path("wvlsol_v1")
    wvlsol_products = PipelineProducts.load(fn)

    if 1:
        from libs.master_calib import load_sky_ref_data

        ref_utdate = "20140316"

        sky_ref_data = load_sky_ref_data(ref_utdate, band)


        ohlines_db = sky_ref_data["ohlines_db"]
        ref_ohline_indices = sky_ref_data["ohline_indices"]


        orders_w_solutions = wvlsol_products["orders"]
        wvl_solutions = wvlsol_products["wvl_sol"]

    if 1: # make aperture

        _o_s = dict(zip(raw_spec_products["orders"], bottomup_solutions))
        ap =  Apertures(orders_w_solutions,
                        [_o_s[o] for o in orders_w_solutions])


    if 1:

        n_slice_one_direction = 2
        n_slice = n_slice_one_direction*2 + 1
        i_center = n_slice_one_direction
        slit_slice = np.linspace(0., 1., n_slice+1)

        slice_center = (slit_slice[i_center], slit_slice[i_center+1])
        slice_up = [(slit_slice[i_center+i], slit_slice[i_center+i+1]) \
                    for i in range(1, n_slice_one_direction+1)]
        slice_down = [(slit_slice[i_center-i-1], slit_slice[i_center-i]) \
                      for i in range(n_slice_one_direction)]

        d = raw_spec_products["combined_image"]
        s_center = ap.extract_spectra_v2(d, slice_center[0], slice_center[1])

        s_up, s_down = [], []
        for s1, s2 in slice_up:
            s = ap.extract_spectra_v2(d, s1, s2)
            s_up.append(s)
        for s1, s2 in slice_down:
            s = ap.extract_spectra_v2(d, s1, s2)
            s_down.append(s)


    if 1:
        # now fit

        #ohline_indices = [ref_ohline_indices[o] for o in orders_w_solutions]


        if 0:
            def test_order(oi):
                ax=subplot(111)
                ax.plot(wvl_solutions[oi], s_center[oi])
                #ax.plot(wvl_solutions[oi], raw_spec_products["specs"][oi])
                o = orders[oi]
                line_indices = ref_ohline_indices[o]
                for li in line_indices:
                    um = np.take(ohlines_db.um, li)
                    intensity = np.take(ohlines_db.intensity, li)
                    ax.vlines(um, ymin=0, ymax=-intensity)




        from libs.reidentify_ohlines import fit_ohlines, fit_ohlines_pixel
        ref_pixel_list, reidentified_lines = \
                        fit_ohlines(ohlines_db, ref_ohline_indices,
                                    orders_w_solutions,
                                    wvl_solutions, s_center)



    if 1:
        # TODO: we should not need this, instead recycle from preivious step.
        fitted_centroid_center = fit_ohlines_pixel(s_center,
                                                   ref_pixel_list)

        d_shift_up = []
        for s in s_up:
            # TODO: ref_pixel_list_filtered need to be updated with recent fit.
            fitted_centroid = fit_ohlines_pixel(s,
                                                ref_pixel_list)
            d_shift = [b-a for a, b in zip(fitted_centroid_center,
                                           fitted_centroid)]
            d_shift_up.append(d_shift)

        d_shift_down = []
        for s in s_down:
            # TODO: ref_pixel_list_filtered need to be updated with recent fit.
            fitted_centroid = fit_ohlines_pixel(s,
                                                ref_pixel_list)
            #fitted_centroid_center,
            d_shift = [b-a for a, b in zip(fitted_centroid_center,
                                           fitted_centroid)]
            d_shift_down.append(d_shift)


    if 1:
        # now fit
        orders = orders_w_solutions

        x_domain = [0, 2048]
        y_domain = [orders[0]-2, orders[-1]+2]


        xl = np.concatenate(fitted_centroid_center)

        yl_ = [o + np.zeros_like(x_) for o, x_ in zip(orders,
                                                      fitted_centroid_center)]
        yl = np.concatenate(yl_)

        from libs.ecfit import fit_2dspec, check_fit_simple

        zl_list = [np.concatenate(d_) for d_ \
                   in d_shift_down[::-1] + d_shift_up]

        pm_list = []
        for zl in zl_list:
            p, m = fit_2dspec(xl, yl, zl,
                              x_degree=1, y_degree=1,
                              x_domain=x_domain, y_domain=y_domain)
            pm_list.append((p,m))

        zz_std_list = []
        for zl, (p, m)  in zip(zl_list, pm_list):
            z_m = p(xl[m], yl[m])
            zz = z_m - zl[m]
            zz_std_list.append(zz.std())

        fig_list = []
        from matplotlib.figure import Figure
        for zl, (p, m)  in zip(zl_list, pm_list):
            fig = Figure()
            check_fit_simple(fig, xl[m], yl[m], zl[m], p, orders)
            fig_list.append(fig)


    if 1:
        xi = np.linspace(0, 2048, 128+1)
        from astropy.modeling import fitting
        from astropy.modeling.polynomial import Chebyshev2D
        x_domain = [0, 2048]
        y_domain = [0., 1.]

        p2_list = []
        for o in orders:
            oi = np.zeros_like(xi) + o
            shift_list = []
            for p,m in pm_list[:n_slice_one_direction]:
                shift_list.append(p(xi, oi))

            shift_list.append(np.zeros_like(xi))

            for p,m in pm_list[n_slice_one_direction:]:
                shift_list.append(p(xi, oi))


            p_init = Chebyshev2D(x_degree=1, y_degree=2,
                                 x_domain=x_domain, y_domain=y_domain)
            f = fitting.LinearLSQFitter()

            yi = 0.5*(slit_slice[:-1] + slit_slice[1:])
            xl, yl = np.meshgrid(xi, yi)
            zl = np.array(shift_list)
            p = f(p_init, xl, yl, zl)

            p2_list.append(p)

    if 1:
        p2_dict = dict(zip(orders, p2_list))

        order_map = ap.make_order_map()
        slitpos_map = ap.make_slitpos_map()

        slitoffset_map = np.empty_like(slitpos_map)
        slitoffset_map.fill(np.nan)
        for o in ap.orders:
            xi = np.arange(0, 2048)
            xl, yl = np.meshgrid(xi, xi)
            msk = order_map == o
            slitoffset_map[msk] = p2_dict[o](xl[msk], slitpos_map[msk])

        import astropy.io.fits as pyfits
        fn = sky_path.get_secondary_path("slitoffset_map.fits")
        pyfits.PrimaryHDU(data=slitoffset_map).writeto(fn, clobber=True)


    if 0:
        # test
        x = np.arange(2048, dtype="d")
        oi = 10
        o = orders[oi]

        yi = 0.5*(slit_slice[:-1] + slit_slice[1:])

        ax1 = subplot(211)
        s1 = s_up[-1][oi]
        s2 = s_down[-1][oi]

        ax1.plot(x, s1)
        ax1.plot(x, s2)

        ax2 = subplot(212, sharex=ax1, sharey=ax1)
        dx1 = p2_dict[o](x, yi[-1]+np.zeros_like(x))
        ax2.plot(x-dx1, s1)

        dx2 = p2_dict[o](x, yi[0]+np.zeros_like(x))
        ax2.plot(x-dx2, s2)
